"""Operaciones git del auditor: clonar por enlace y publicar la rama de auditoría.

Reglas de seguridad:
- El código del objetivo nunca se ejecuta; los hooks de git se desactivan en el clon.
- La única escritura remota es una rama nueva `audit/<run_id>` con archivos bajo `.audit/<run_id>/`.
- Nunca se hace force push ni se escribe en la rama auditada.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .common import load_json, sanitize_url

NO_HOOKS = ["-c", "core.hooksPath=/dev/null"]
AUDIT_IDENTITY = ["-c", "user.name=dlc.audit", "-c", "user.email=dlc-audit@users.noreply.github.com"]


class GitError(RuntimeError):
    pass


def _run(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, env=env, timeout=600)
    if check and proc.returncode != 0:
        raise GitError(f"git {' '.join(args[:3])} falló: {sanitize_url(proc.stderr.strip() or proc.stdout.strip())}")
    return proc


def safe_source(source: str) -> bool:
    """Acepta URL https/ssh/git@ o ruta local existente; rechaza opciones disfrazadas."""
    if source.startswith("-") or "\n" in source:
        return False
    return bool(re.match(r"^(https?://|ssh://|git@[\w.-]+:|file://)", source)) or Path(source).is_dir()


def repo_name(source: str) -> str:
    tail = re.split(r"[/:]", source.rstrip("/"))[-1]
    return re.sub(r"\.git$", "", tail) or "repo"


def resolve_ref(repo: Path, ref: str) -> str:
    for candidate in (f"origin/{ref}", ref):
        out = _run(["rev-parse", "--verify", "-q", f"{candidate}^{{commit}}"], cwd=repo, check=False)
        if out.returncode == 0:
            return out.stdout.strip()
    raise GitError(f"No se encontró la referencia '{ref}' en el repositorio.")


def fetch(source: str, dest_root: Path, ref: str | None = None) -> dict:
    """Clona (o actualiza) `source` en dest_root/<nombre> y deja el árbol en `ref` desacoplado."""
    if not safe_source(source):
        raise GitError("Fuente no válida: use una URL https/ssh o una ruta local a un repositorio.")
    dest = dest_root / repo_name(source)
    dest_root.mkdir(parents=True, exist_ok=True)
    if (dest / ".git").is_dir():
        _run([*NO_HOOKS, "fetch", "--all", "--prune", "--tags", "-q"], cwd=dest)
    else:
        _run([*NO_HOOKS, "clone", "-q", "--", source, str(dest)])
    if ref is None:
        head = _run(["symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD"], cwd=dest, check=False).stdout.strip()
        ref = head.removeprefix("origin/") or "HEAD"
    sha = resolve_ref(dest, ref) if ref != "HEAD" else _run(["rev-parse", "HEAD"], cwd=dest).stdout.strip()
    _run([*NO_HOOKS, "checkout", "-q", "--detach", sha], cwd=dest)
    return {"path": str(dest), "ref": ref, "revision": sha, "url": sanitize_url(source)}


def read_remote_file(repo: Path, ref: str, path: str) -> str:
    """Lee un archivo de una rama remota sin cambiar el árbol de trabajo."""
    return _run(["show", f"origin/{ref}:{path}"], cwd=repo).stdout


def publish(run_path: Path, push: bool = False, remote_url: str | None = None) -> dict:
    """Crea (y opcionalmente empuja) la rama audit/<run_id> con los entregables del run."""
    from .validate import validate_run  # evitar import circular

    run = load_json(run_path)
    errors, _ = validate_run(run, final=True)
    if errors:
        raise GitError("El run no pasa validate --final: " + "; ".join(errors[:3]))
    run_dir = run_path.parent
    for needed in ("informe.md", "hallazgos.json"):
        if not (run_dir / needed).is_file():
            raise GitError(f"Falta {needed}; ejecute render antes de publicar.")

    target = Path(run["target"]["path"])
    revision = run["target"]["revision"]
    if not (target / ".git").exists() or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise GitError("El objetivo no es un clon git con revisión conocida; no se puede publicar.")
    url = remote_url or _run(["remote", "get-url", "origin"], cwd=target).stdout.strip()
    if not safe_source(url):
        raise GitError("URL remota no válida.")
    branch = f"audit/{run['run_id']}"
    prefix = f".audit/{run['run_id']}/"

    if _run(["ls-remote", "--heads", url, branch], check=False).stdout.strip():
        raise GitError(f"La rama {branch} ya existe en el remoto; cada run publica una rama nueva.")

    files = [p for p in run_dir.rglob("*") if p.is_file()]
    work = Path(tempfile.mkdtemp(prefix="dlc-audit-publish-"))
    try:
        clone = work / "clone"
        _run([*NO_HOOKS, "clone", "-q", "--no-checkout", "--", str(target), str(clone)])
        # La revisión auditada puede estar solo en refs/remotes/* o desacoplada del clon de trabajo.
        _run([*NO_HOOKS, "fetch", "-q", str(target), "+refs/*:refs/dlc-src/*", "HEAD:refs/dlc-src/head"], cwd=clone)
        _run([*NO_HOOKS, "checkout", "-q", "-b", branch, revision], cwd=clone)
        for f in files:
            dest = clone / prefix / f.relative_to(run_dir).as_posix()
            dest.parent.mkdir(parents=True, exist_ok=True)
            if f == run_path:
                # La ruta local del clon no debe salir del equipo del auditor.
                public = load_json(f)
                public["target"]["path"] = "(local)"
                dest.write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
            else:
                shutil.copyfile(f, dest)
        _run(["add", "--", ".audit"], cwd=clone)
        n = len(run["findings"])
        _run([*NO_HOOKS, *AUDIT_IDENTITY, "commit", "-q", "-m",
              f"Auditoría {run['run_id']}: {n} hallazgo(s), ronda {run.get('round', 1)}"], cwd=clone)

        changed = _run(["diff", "--name-only", revision, "HEAD"], cwd=clone).stdout.split()
        outside = [c for c in changed if not c.startswith(prefix)]
        if outside or not changed:
            raise GitError(f"Guardián: la rama toca rutas fuera de {prefix}: {outside[:3]}")

        result = {"branch": branch, "base_revision": revision, "files": changed, "pushed": False, "url": sanitize_url(url)}
        if push:
            _run([*NO_HOOKS, "push", "-q", url, f"{branch}:refs/heads/{branch}"], cwd=clone)
            result["pushed"] = True
        return result
    finally:
        shutil.rmtree(work, ignore_errors=True)
