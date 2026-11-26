"""Skills portables: fuente única en skills/, copias generadas y validación de portabilidad.

Decisiones (docs/multiplataforma.md):
- skills/ es la única fuente editable.
- .claude/skills/ (Claude Code) y .agents/skills/ (Codex y Antigravity) son copias byte a byte.
- Nadie edita las copias; `check` falla si difieren de la fuente.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import zipfile
from pathlib import Path

from .common import ROOT, ensure_outside_repo, workdir
from .scan import parse_frontmatter

SOURCE = "skills"
TARGETS = (".claude/skills", ".agents/skills")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
XML_LIKE = re.compile(r"<[^>]*>")
LINK_RE = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")
MAX_LINES = 500
FORBIDDEN = (
    ("argument-hint", "campo propietario de Claude Code"),
    ("$ARGUMENTS", "variable propietaria de Claude Code"),
    ("AskUserQuestion", "herramienta propietaria de Claude Code"),
    (".claude/", "ruta propietaria de Claude Code"),
)
ZIP_DATE = (2026, 1, 1, 0, 0, 0)


def list_skills(root: Path = ROOT) -> list[Path]:
    base = root / SOURCE
    if not base.is_dir():
        return []
    return sorted(d for d in base.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())


def _files(directory: Path) -> dict[str, str]:
    """{ruta relativa con '/': sha256} de los archivos de una carpeta, sin cachés."""
    found: dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(directory):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            path = Path(dirpath) / name
            rel = path.relative_to(directory).as_posix()
            found[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def check_portability(root: Path = ROOT) -> list[str]:
    """Errores de portabilidad de las skills fuente (lista vacía si todo cumple)."""
    errors: list[str] = []
    skills = list_skills(root)
    if not skills:
        return [f"No hay skills en {SOURCE}/."]
    for skill in skills:
        label = f"{SOURCE}/{skill.name}"
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if fm is None:
            errors.append(f"{label}/SKILL.md: sin frontmatter.")
            continue
        extra = sorted(set(fm) - {"name", "description"})
        if extra:
            errors.append(f"{label}/SKILL.md: campos no portables en el frontmatter: {', '.join(extra)} "
                          "(solo name y description).")
        name, desc = fm.get("name", ""), fm.get("description", "")
        if not name:
            errors.append(f"{label}/SKILL.md: falta name.")
        else:
            if not NAME_RE.fullmatch(name) or len(name) > 64:
                errors.append(f"{label}/SKILL.md: name '{name}' inválido (minúsculas, números y guiones; máximo 64).")
            if name != skill.name:
                errors.append(f"{label}/SKILL.md: name '{name}' no coincide con la carpeta '{skill.name}'.")
            if re.search(r"claude|anthropic", name, re.I):
                errors.append(f"{label}/SKILL.md: name '{name}' no puede contener 'claude' ni 'anthropic'.")
        if not desc.strip():
            errors.append(f"{label}/SKILL.md: falta description.")
        else:
            if len(desc) > 1024:
                errors.append(f"{label}/SKILL.md: description de {len(desc)} caracteres (máximo 1024).")
            if XML_LIKE.search(desc) or XML_LIKE.search(name):
                errors.append(f"{label}/SKILL.md: name o description contienen etiquetas tipo XML (<...>).")
        if len(text.splitlines()) > MAX_LINES:
            errors.append(f"{label}/SKILL.md: más de {MAX_LINES} líneas; mueva el detalle a references/ (regla propia).")
        for rel in sorted(_files(skill)):
            if not rel.endswith(".md"):
                continue
            content = (skill / rel).read_text(encoding="utf-8")
            for token, why in FORBIDDEN:
                if token in content:
                    errors.append(f"{label}/{rel}: contiene '{token}' ({why}); use una redacción general.")
        in_fence = False
        for line in text.splitlines():
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for ref in LINK_RE.findall(line):
                if re.match(r"^[a-z][a-z0-9+.-]*:", ref) or ref.startswith(("/", "$")):
                    continue
                if not (skill / ref).exists():
                    errors.append(f"{label}/SKILL.md: enlace roto a '{ref}'.")
    return errors


def check_sync(root: Path = ROOT) -> list[str]:
    """Diferencias entre skills/ y sus copias generadas (lista vacía si coinciden)."""
    errors: list[str] = []
    names = {s.name for s in list_skills(root)}
    for target in TARGETS:
        tdir = root / target
        for skill in list_skills(root):
            src, dst = _files(skill), (_files(tdir / skill.name) if (tdir / skill.name).is_dir() else None)
            if dst is None:
                errors.append(f"falta {target}/{skill.name}/")
                continue
            for rel in sorted(src.keys() - dst.keys()):
                errors.append(f"falta {target}/{skill.name}/{rel}")
            for rel in sorted(dst.keys() - src.keys()):
                errors.append(f"sobrante {target}/{skill.name}/{rel}")
            for rel in sorted(k for k in src.keys() & dst.keys() if src[k] != dst[k]):
                errors.append(f"distinto {target}/{skill.name}/{rel}")
        if tdir.is_dir():
            for d in sorted(p for p in tdir.iterdir() if p.is_dir() and p.name not in names):
                errors.append(f"sobrante {target}/{d.name}/ (no existe en {SOURCE}/)")
    return errors


def sync(root: Path = ROOT) -> list[str]:
    """Regenera las copias desde skills/. Se niega si la fuente no es portable."""
    problems = check_portability(root)
    if problems:
        raise ValueError("La fuente no es portable; corrija antes de sincronizar:\n- " + "\n- ".join(problems))
    actions: list[str] = []
    names = {s.name for s in list_skills(root)}
    for target in TARGETS:
        tdir = root / target
        tdir.mkdir(parents=True, exist_ok=True)
        for old in sorted(p for p in tdir.iterdir() if p.is_dir() and p.name not in names):
            shutil.rmtree(old)
            actions.append(f"eliminado {target}/{old.name}/ (no existe en {SOURCE}/)")
        for skill in list_skills(root):
            dst = tdir / skill.name
            if dst.is_dir() and _files(dst) == _files(skill):
                continue
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(skill, dst, ignore=shutil.ignore_patterns("__pycache__"))
            actions.append(f"generado {target}/{skill.name}/")
    return actions


def package_zip(root: Path = ROOT, out_dir: Path | None = None) -> Path:
    """Empaqueta todas las skills en un .zip (una carpeta por skill) para subirlo a ChatGPT.

    El formato de subida de ChatGPT no está documentado [No verificado]: es el empaquetado habitual
    del estándar Agent Skills. Se escribe en el directorio temporal, nunca en este repositorio.
    """
    problems = check_portability(root)
    if problems:
        raise ValueError("La fuente no es portable:\n- " + "\n- ".join(problems))
    out_dir = ensure_outside_repo(out_dir if out_dir else workdir() / "packages")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "dlc-audit-skills.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for skill in list_skills(root):
            for rel in sorted(_files(skill)):
                info = zipfile.ZipInfo(f"{skill.name}/{rel}", ZIP_DATE)
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, (skill / rel).read_bytes())
    return path
