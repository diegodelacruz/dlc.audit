"""Verifica el cierre del integrador contra el repositorio real (no se confía en lo declarado)."""
from __future__ import annotations

import re
from pathlib import Path

from .gitops import _run

STATUSES = ("fixed", "not_applicable", "not_fixed", "partial")
NEEDS_NOTE = ("not_applicable", "not_fixed", "partial")
HEX = re.compile(r"^[0-9a-f]{7,40}$")
REQUIRED = ("run_id", "base_revision", "head_revision", "branch", "findings")


def _git_ok(repo: Path, *args: str) -> bool:
    return _run(list(args), cwd=repo, check=False).returncode == 0


def check_closure(baseline: dict, cierre: dict, repo: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    for key in REQUIRED:
        if key not in cierre:
            errors.append(f"cierre: falta '{key}'.")
    if errors:
        return {"errors": errors, "warnings": warnings, "changed_files": [], "claims": {}}

    base, head = baseline["target"]["revision"], str(cierre["head_revision"])
    # El cierre es dato no confiable: ningún valor llega a git sin validarse como SHA.
    if not HEX.match(head):
        errors.append(f"cierre: head_revision inválida ({head[:40]!r}); se esperaba un SHA hexadecimal.")
        return {"errors": errors, "warnings": warnings, "changed_files": [], "claims": {}}
    if not HEX.match(str(base)):
        errors.append("cierre: la revisión del baseline no es un SHA válido.")
        return {"errors": errors, "warnings": warnings, "changed_files": [], "claims": {}}
    if cierre["run_id"] != baseline["run_id"]:
        errors.append(f"cierre: run_id {cierre['run_id']} no corresponde al baseline {baseline['run_id']}.")
    if cierre["base_revision"] != base:
        errors.append("cierre: base_revision no coincide con la revisión auditada en el baseline.")

    changed: list[str] = []
    in_range: set[str] = set()
    if not _git_ok(repo, "cat-file", "-e", f"{head}^{{commit}}"):
        errors.append(f"cierre: head_revision {head[:12]} no existe en el repositorio (¿falta el push?).")
    else:
        if not _git_ok(repo, "merge-base", "--is-ancestor", base, head):
            errors.append("cierre: head_revision no desciende de la revisión auditada (historia reescrita o rama distinta).")
        else:
            changed = _run(["diff", "--name-only", base, head], cwd=repo).stdout.split()
            in_range = set(_run(["rev-list", f"{base}..{head}"], cwd=repo).stdout.split())
        if any(c.startswith(".audit/") for c in changed):
            warnings.append("cierre: la rama del integrador contiene archivos de .audit/ (no debe fusionar la rama del auditor).")
        tree = _run(["ls-tree", "-r", "--name-only", head, "--", ".audit"], cwd=repo, check=False).stdout.strip()
        if tree and not any(c.startswith(".audit/") for c in changed):
            warnings.append("cierre: el árbol auditado contiene .audit/ (fue incorporado antes de esta ronda).")

    expected = {f["id"] for f in baseline["findings"]}
    seen: set[str] = set()
    claimed_files: set[str] = set()
    claims = {s: 0 for s in STATUSES}
    for item in cierre["findings"]:
        fid = item.get("id")
        if fid in seen:
            errors.append(f"cierre: {fid} aparece más de una vez.")
        seen.add(fid)
        if fid not in expected:
            errors.append(f"cierre: {fid} no existe en el baseline.")
            continue
        status = item.get("status")
        if status not in STATUSES:
            errors.append(f"cierre: {fid} tiene status inválido ({status!r}); use {', '.join(STATUSES)}.")
            continue
        claims[status] += 1
        if status in NEEDS_NOTE and not str(item.get("note", "")).strip():
            errors.append(f"cierre: {fid} ({status}) requiere 'note' con el motivo.")
        if status in ("fixed", "partial"):
            if not item.get("verification"):
                warnings.append(f"cierre: {fid} sin 'verification'.")
            commits = item.get("commits") or []
            if status == "fixed" and not commits:
                errors.append(f"cierre: {fid} (fixed) sin commits.")
            for c in commits:
                if not HEX.match(str(c)):
                    errors.append(f"cierre: {fid} cita un commit inválido ({str(c)[:40]!r}).")
                    continue
                full = _run(["rev-parse", "--verify", "-q", f"{c}^{{commit}}"], cwd=repo, check=False).stdout.strip()
                if not full:
                    errors.append(f"cierre: {fid} cita el commit {c} que no existe.")
                elif in_range and full not in in_range:
                    warnings.append(f"cierre: {fid} cita el commit {c[:10]} fuera del rango auditado..head.")
            for f in item.get("files") or []:
                claimed_files.add(f)
                if changed and f not in changed:
                    warnings.append(f"cierre: {fid} declara haber cambiado {f}, pero no figura en el diff.")
    for missing in sorted(expected - seen):
        errors.append(f"cierre: falta el hallazgo {missing}.")

    declared_extra = {x.get("path") for x in cierre.get("out_of_scope_changes", [])}
    for path in changed:
        if path not in claimed_files and path not in declared_extra:
            warnings.append(f"deriva: {path} cambió y ningún hallazgo ni 'out_of_scope_changes' lo declara.")

    return {"errors": errors, "warnings": warnings, "changed_files": changed, "claims": claims,
            "base_revision": base, "head_revision": head, "contradicted": []}


def cross_check(check: dict, cierre: dict, new_run: dict) -> dict:
    """Marca como contradichas las correcciones declaradas que la nueva auditoría sigue detectando."""
    still_open = {f["id"] for f in new_run["findings"]}
    check["contradicted"] = sorted(
        i["id"] for i in cierre["findings"] if i.get("status") == "fixed" and i.get("id") in still_open)
    return check
