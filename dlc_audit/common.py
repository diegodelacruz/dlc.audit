"""Utilidades compartidas: catálogo, perfil, huella de hallazgos, git."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_VERSION = "1.0"

SEVERITIES = ("critical", "high", "medium", "low", "info")
CONFIDENCES = ("verified", "inferential", "unverified")
EFFORTS = ("S", "M", "L")
RULE_STATUSES = ("evaluated", "not_applicable", "pending")
METHODS = ("deterministic", "judgment")
DETECTORS = ("scan", "agent")
EVIDENCE_TYPES = ("file", "absence")

CONFIDENCE_LABEL = {
    "verified": "Verificado",
    "inferential": "[Inferencial]",
    "unverified": "[No verificado]",
}


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def load_profile(name: str = "default", root: Path = ROOT) -> dict:
    path = root / "profiles" / f"{name}.json"
    if not path.is_file():
        raise SystemExit(f"Perfil no encontrado: {path}")
    return load_json(path)


def load_catalog(profile: dict, root: Path = ROOT, as_of: dt.date | None = None) -> dict:
    """Devuelve {rule_id: rule} con reglas vigentes y habilitadas en el perfil."""
    as_of = as_of or dt.date.today()
    rules: dict[str, dict] = {}
    for name in profile["catalogs"]:
        path = root / "rules" / f"{name}.json"
        if not path.is_file():
            raise SystemExit(f"Catálogo no encontrado: {path}")
        for rule in load_json(path)["rules"]:
            if rule["id"] in profile.get("disabled_rules", []):
                continue
            if dt.date.fromisoformat(rule["valid_from"]) > as_of:
                continue
            if rule.get("valid_to") and dt.date.fromisoformat(rule["valid_to"]) < as_of:
                continue
            rule = dict(rule)
            rule["severity"] = profile.get("severity_overrides", {}).get(rule["id"], rule["severity"])
            rules[rule["id"]] = rule
    return rules


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def finding_id(rule_id: str, evidence: list[dict]) -> str:
    """Huella estable: regla + tipo + ruta + extracto normalizado (sin líneas)."""
    first = evidence[0]
    raw = "|".join([rule_id, first["type"], first["path"], normalize(first.get("excerpt", ""))])
    return f"{rule_id}-{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:10]}"


def _git(path: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def git_info(path: Path) -> dict:
    revision = _git(path, "rev-parse", "HEAD")
    status = _git(path, "status", "--porcelain")
    return {"revision": revision or "no-git", "dirty": bool(status)}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
