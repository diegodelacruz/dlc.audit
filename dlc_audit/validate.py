"""Validación del run: estructura, catálogo y evidencia contra el archivo real."""
from __future__ import annotations

from pathlib import Path

from .common import (
    CONFIDENCES, DETECTORS, EFFORTS, EVIDENCE_TYPES, METHODS, ROOT, RULE_STATUSES, SCHEMA_VERSION,
    SEVERITIES, finding_id, load_catalog, load_profile, normalize,
)

REQUIRED_FINDING = ("rule_id", "rule_version", "severity", "confidence", "title", "description",
                    "evidence", "recommendation", "effort", "change_group", "detected_by", "status")
REQUIRED_RUN = ("schema_version", "run_id", "auditor", "profile", "target", "coverage", "rules",
                "executive_summary", "limitations", "findings")


def _check_evidence(ev: dict, target: Path | None, label: str, errors: list[str]) -> bool:
    """Devuelve True si la evidencia fue comprobada contra el archivo real."""
    if ev.get("type") not in EVIDENCE_TYPES:
        errors.append(f"{label}: evidence.type inválido ({ev.get('type')!r}).")
        return False
    path = ev.get("path")
    if not path or path.startswith("/") or ".." in Path(path).parts or "\\" in path:
        errors.append(f"{label}: evidence.path debe ser relativo y con '/' ({path!r}).")
        return False
    if target is None:
        return False
    full = target / path
    if ev["type"] == "absence":
        if full.exists():
            errors.append(f"{label}: se declara ausencia pero {path} existe.")
            return False
        return True
    if not full.is_file():
        errors.append(f"{label}: {path} no existe en el objetivo.")
        return False
    if ev["type"] == "file_size":
        size = ev.get("size_bytes")
        if not isinstance(size, int) or isinstance(size, bool):
            errors.append(f"{label}: file_size exige 'size_bytes' entero ({size!r}).")
            return False
        real = full.stat().st_size
        if size != real:
            errors.append(f"{label}: size_bytes {size} no coincide con el tamaño real de {path} ({real}).")
            return False
        return True
    ls, le = ev.get("line_start"), ev.get("line_end")
    if not isinstance(ls, int) or not isinstance(le, int) or ls < 1 or le < ls:
        errors.append(f"{label}: líneas inválidas ({ls}-{le}).")
        return False
    lines = full.read_text(encoding="utf-8", errors="replace").splitlines()
    if le > len(lines):
        errors.append(f"{label}: {path} tiene {len(lines)} líneas; se cita hasta {le}.")
        return False
    if ev.get("redacted"):
        return True
    excerpt = normalize(ev.get("excerpt", ""))
    if not excerpt:
        errors.append(f"{label}: evidencia sin extracto.")
        return False
    if excerpt not in normalize("\n".join(lines[ls - 1:le])):
        errors.append(f"{label}: el extracto no coincide con {path}:{ls}-{le}.")
        return False
    return True


def validate_run(run: dict, target: Path | None = None, final: bool = False,
                 assign_ids: bool = False, root: Path = ROOT) -> tuple[list[str], list[str]]:
    """Devuelve (errores, avisos). Con assign_ids completa los ids faltantes en el propio dict."""
    errors: list[str] = []
    warnings: list[str] = []

    for key in REQUIRED_RUN:
        if key not in run:
            errors.append(f"Falta el campo '{key}' en el run.")
    if errors:
        return errors, warnings
    if run["schema_version"] != SCHEMA_VERSION:
        errors.append(f"schema_version {run['schema_version']!r} no soportada (se esperaba {SCHEMA_VERSION}).")

    if target is None and run["target"].get("path"):
        candidate = Path(run["target"]["path"])
        target = candidate if candidate.is_dir() else None
    if target is None:
        warnings.append("No se pudo localizar el objetivo: la evidencia no se verificó contra archivos.")

    try:
        catalog = load_catalog(load_profile(run["profile"]["name"], root), root)
    except SystemExit as exc:
        return [str(exc)], warnings

    rule_ids = set()
    for r in run["rules"]:
        rid = r.get("id")
        rule_ids.add(rid)
        if rid not in catalog:
            errors.append(f"rules: {rid} no está en el catálogo vigente del perfil.")
        if r.get("status") not in RULE_STATUSES:
            errors.append(f"rules: {rid} tiene status inválido ({r.get('status')!r}).")
        if r.get("method") not in METHODS:
            errors.append(f"rules: {rid} tiene method inválido.")
        if r.get("status") == "not_applicable" and not r.get("note"):
            errors.append(f"rules: {rid} es not_applicable sin 'note'.")
        if r.get("status") == "pending":
            (errors if final else warnings).append(f"rules: {rid} sigue pendiente de evaluación.")
    for rid in catalog:
        if rid not in rule_ids:
            warnings.append(f"rules: {rid} del catálogo no figura en el run.")

    seen: dict[str, int] = {}
    for idx, f in enumerate(run["findings"]):
        label = f"findings[{idx}]"
        for key in REQUIRED_FINDING:
            if key not in f:
                errors.append(f"{label}: falta '{key}'.")
        if any(k not in f for k in REQUIRED_FINDING):
            continue
        for key, allowed in (("severity", SEVERITIES), ("confidence", CONFIDENCES),
                             ("effort", EFFORTS), ("detected_by", DETECTORS)):
            if f[key] not in allowed:
                errors.append(f"{label}: {key} inválido ({f[key]!r}).")
        if f["status"] != "open":
            errors.append(f"{label}: en Fase 1 status debe ser 'open'.")
        rule = catalog.get(f["rule_id"])
        if rule is None:
            errors.append(f"{label}: regla {f['rule_id']} fuera del catálogo.")
        elif f["rule_version"] != rule["version"]:
            errors.append(f"{label}: rule_version {f['rule_version']} distinta de la vigente {rule['version']}.")
        if f["rule_id"] not in rule_ids:
            errors.append(f"{label}: la regla {f['rule_id']} no figura en rules[].")
        for r in run["rules"]:
            if r.get("id") == f["rule_id"] and r.get("status") != "evaluated":
                errors.append(f"{label}: hay hallazgo de {f['rule_id']} pero la regla está '{r.get('status')}'.")
        if not f["title"].strip() or not f["description"].strip() or not f["recommendation"].strip():
            errors.append(f"{label}: title, description y recommendation no pueden estar vacíos.")
        if not f["evidence"]:
            errors.append(f"{label}: sin evidencia.")
            continue
        checked = [_check_evidence(ev, target, f"{label}", errors) for ev in f["evidence"]]
        if f["confidence"] == "verified" and target is not None and not all(checked):
            errors.append(f"{label}: 'verified' exige evidencia comprobada contra el objetivo.")
        expected = finding_id(f["rule_id"], f["evidence"])
        if not f.get("id"):
            if assign_ids:
                f["id"] = expected
            else:
                errors.append(f"{label}: falta 'id' (use --assign-ids).")
                continue
        elif f["id"] != expected:
            errors.append(f"{label}: id {f['id']} no coincide con la huella {expected}.")
        if f["id"] in seen:
            errors.append(f"{label}: id duplicado con findings[{seen[f['id']]}] ({f['id']}); diferencie la evidencia.")
        seen[f["id"]] = idx

    if final:
        if not run["executive_summary"].strip():
            errors.append("executive_summary vacío.")
        if not run["limitations"]:
            errors.append("limitations vacío: declare al menos los límites de la revisión.")
        if not run.get("finished_at"):
            errors.append("finished_at vacío (se completa con validate --final).")
    return errors, warnings
