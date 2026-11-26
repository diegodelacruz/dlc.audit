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


SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/@+-]*$")
RUN_ID_RE = re.compile(r"^\d{8}T\d{4,6}Z-[\w.-]+$")


def _same_repo(a: str, b: str) -> bool:
    """Compara dos orígenes (URL o ruta) ignorando credenciales, barra final y sufijo .git."""
    def norm(x: str) -> str:
        x = sanitize_url(x).rstrip("/")
        p = Path(x)
        if p.is_dir():
            x = str(p.resolve())
        return re.sub(r"\.git$", "", x)
    return norm(a) == norm(b)


def repo_name(source: str) -> str:
    tail = re.split(r"[/:]", source.rstrip("/"))[-1]
    return re.sub(r"\.git$", "", tail) or "repo"


def resolve_ref(repo: Path, ref: str) -> str:
    if not SAFE_REF.match(ref) or ".." in ref:
        raise GitError(f"Referencia no válida: {ref!r}.")
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
        origin = _run(["remote", "get-url", "origin"], cwd=dest, check=False).stdout.strip()
        if not _same_repo(origin, source):
            raise GitError(f"{dest} ya contiene otro repositorio ({sanitize_url(origin)}); use otra carpeta con --dest.")
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

    # Solo los entregables conocidos: nunca archivos sueltos que haya en la carpeta del run.
    files = [p for p in run_dir.rglob("*") if p.is_file() and (
        p.relative_to(run_dir).as_posix() in ("hallazgos.json", "informe.md", "prompt-integrador.md")
        or (p.parent == run_dir / "prompts" and p.suffix == ".md"))]
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


# ---------------------------------------------------------------- cierre del ciclo

BRANCH_RE = re.compile(r"^audit/\d{8}T\d{4,6}Z-[\w.-]+$")


def default_branch(repo: Path) -> str:
    head = _run(["symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD"], cwd=repo, check=False).stdout.strip()
    return head.removeprefix("origin/") or "main"


def _remote_branch_exists(repo: Path, branch: str) -> bool:
    return _run(["rev-parse", "--verify", "-q", f"refs/remotes/origin/{branch}"], cwd=repo, check=False).returncode == 0


def cycle_branches(repo: Path, final_run: dict) -> tuple[list[dict], list[str]]:
    """Ramas audit/* del ciclo: se siguen los baseline_run_id desde el run final, leyendo cada rama del remoto."""
    found: list[dict] = []
    notes: list[str] = []
    ids: list[str] = []
    if _remote_branch_exists(repo, f"audit/{final_run['run_id']}"):
        ids.append(final_run["run_id"])
    rid, seen = final_run.get("baseline_run_id"), set(ids)
    while rid and rid not in seen:
        if not isinstance(rid, str) or not RUN_ID_RE.match(rid):
            notes.append(f"baseline_run_id inválido en la cadena ({str(rid)[:40]!r}); se detiene aquí.")
            break
        seen.add(rid)
        ids.append(rid)
        branch = f"audit/{rid}"
        if not _remote_branch_exists(repo, branch):
            notes.append(f"La rama {branch} ya no existe en el remoto; la cadena se corta aquí.")
            ids.pop()
            break
        data = json.loads(read_remote_file(repo, branch, f".audit/{rid}/hallazgos.json"))
        rid = data.get("baseline_run_id")
    for rid in ids:
        branch = f"audit/{rid}"
        data = json.loads(read_remote_file(repo, branch, f".audit/{rid}/hallazgos.json"))
        found.append({"run_id": rid, "branch": branch, "base_revision": data["target"]["revision"]})
    return found, notes


def _archive_branch(repo: Path, entry: dict, archive_dir: Path) -> int:
    """Copia .audit/<run_id>/ de la rama a archive_dir/<run_id>/ sin sobrescribir lo existente."""
    prefix = f".audit/{entry['run_id']}/"
    names = _run(["ls-tree", "-r", "--name-only", f"origin/{entry['branch']}", "--", prefix], cwd=repo).stdout.split("\n")
    copied = 0
    for name in filter(None, names):
        dest = archive_dir / entry["run_id"] / name[len(prefix):]
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(read_remote_file(repo, entry["branch"], name), encoding="utf-8", newline="\n")
        copied += 1
    return copied


def cleanup(repo: Path, final_run: dict, archive_dir: Path, delete: bool = False,
            allow_observations: bool = False) -> dict:
    """Archiva y (con delete=True) borra del remoto las ramas audit/* del ciclo aprobado."""
    from .common import load_profile, verdict
    from .validate import validate_run

    errors, _ = validate_run(final_run, repo, final=True)
    if errors:
        raise GitError("El run final no pasa validate --final: " + "; ".join(errors[:3]))
    dictamen = verdict(final_run["findings"], load_profile(final_run["profile"]["name"]))
    allowed = ("APROBADO", "APROBADO CON OBSERVACIONES") if allow_observations else ("APROBADO",)
    if dictamen not in allowed:
        raise GitError(f"El dictamen es {dictamen}: el ciclo no está cerrado; no se borra nada.")

    _run([*NO_HOOKS, "fetch", "--all", "--prune", "-q"], cwd=repo)
    url = _run(["remote", "get-url", "origin"], cwd=repo).stdout.strip()
    entries, notes = cycle_branches(repo, final_run)
    report = {"verdict": dictamen, "deleted": [], "refused": [], "kept": [], "archived": 0, "notes": notes,
              "dry_run": not delete}
    for e in entries:
        branch, rid = e["branch"], e["run_id"]
        if not BRANCH_RE.match(branch):
            report["refused"].append({"branch": branch, "reason": "nombre fuera del patrón audit/<run_id>"})
            continue
        tip = _run(["rev-parse", f"origin/{branch}"], cwd=repo).stdout.strip()
        # publish crea exactamente un commit cuyo padre es la revisión auditada.
        parents = _run(["rev-list", "--parents", "-n", "1", tip], cwd=repo).stdout.split()[1:]
        changed = _run(["diff", "--name-only", e["base_revision"], tip], cwd=repo, check=False).stdout.split()
        outside = [c for c in changed if not c.startswith(f".audit/{rid}/")][:3]
        if parents != [e["base_revision"]] or not changed or outside:
            why = []
            if parents != [e["base_revision"]]:
                why.append("no es un único commit sobre la revisión auditada (hay commits adicionales o historia distinta)")
            if outside:
                why.append(f"cambios fuera de .audit/{rid}/: {outside}")
            if not changed:
                why.append("sin cambios")
            report["refused"].append({"branch": branch, "reason": "; ".join(why)})
            continue
        report["archived"] += _archive_branch(repo, e, archive_dir)
        if delete:
            _run([*NO_HOOKS, "push", "-q", url, "--delete", branch], cwd=repo)
            report["deleted"].append(branch)
        else:
            report["kept"].append(branch)
    if delete:
        _run([*NO_HOOKS, "fetch", "--prune", "-q"], cwd=repo, check=False)
    others = _run(["for-each-ref", "--format=%(refname:strip=3)", "refs/remotes/origin/audit/"], cwd=repo).stdout.split()
    mine = {e["branch"] for e in entries}
    report["not_in_cycle"] = sorted(b for b in others if b not in mine)
    return report
