"""Genera informe.md y prompts de cambio desde el JSON del run."""
from __future__ import annotations

import re
from pathlib import Path
from string import Template

from .common import CONFIDENCE_LABEL, ROOT, SEVERITIES, load_catalog, load_profile, normalize

SEV_ES = {"critical": "Crítica", "high": "Alta", "medium": "Media", "low": "Baja", "info": "Informativa"}
EFFORT_ES = {"S": "S (menos de 1 h)", "M": "M (menos de 1 día)", "L": "L (más de 1 día)"}


def _template(name: str, root: Path) -> Template:
    return Template((root / "templates" / name).read_text(encoding="utf-8"))


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "grupo"


def _fence(text: str) -> str:
    return "```" if "```" not in text else "~~~~"


def _evidence_md(finding: dict) -> str:
    lines = []
    for ev in finding["evidence"]:
        if ev["type"] == "absence":
            lines.append(f"- `{ev['path']}`: {ev.get('note', 'no existe')}")
            continue
        loc = f"{ev['path']}:{ev['line_start']}" + (f"-{ev['line_end']}" if ev["line_end"] != ev["line_start"] else "")
        tag = " (valor redactado)" if ev.get("redacted") else ""
        fence = _fence(ev["excerpt"])
        lines.append(f"- `{loc}`{tag}\n\n{fence}\n{ev['excerpt']}\n{fence}\n")
    return "\n".join(lines)


def _sorted_findings(findings: list[dict]) -> list[dict]:
    return sorted(findings, key=lambda f: (SEVERITIES.index(f["severity"]), f["rule_id"], f["id"]))


def _groups(findings: list[dict]) -> list[tuple[str, list[dict]]]:
    groups: dict[str, list[dict]] = {}
    for f in _sorted_findings(findings):
        groups.setdefault(f["change_group"], []).append(f)
    return sorted(groups.items(), key=lambda kv: (SEVERITIES.index(kv[1][0]["severity"]), kv[0]))


def render_prompts(run: dict, out_dir: Path, root: Path = ROOT) -> list[tuple[str, str, list[dict]]]:
    profile = load_profile(run["profile"]["name"], root)
    catalog = load_catalog(profile, root)
    conventions_cfg = profile.get("prompt_conventions", {})
    tmpl = _template("prompt-cambio.md.tmpl", root)
    prompts_dir = out_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    for old in prompts_dir.glob("*.md"):
        old.unlink()

    index = []
    for n, (group, items) in enumerate(_groups(run["findings"]), 1):
        number = f"{n:02d}"
        domains = {catalog[f["rule_id"]]["domain"] for f in items if f["rule_id"] in catalog}
        conv = list(conventions_cfg.get("*", []))
        for d in sorted(domains):
            conv += conventions_cfg.get(d, [])
        conventions = "\n".join(f"- {c}" for c in dict.fromkeys(conv))

        paths = sorted({ev["path"] for f in items for ev in f["evidence"]})
        scope = "\n".join(f"- `{p}`" for p in paths)

        blocks, acceptance, seen_rules = [], [], set()
        for f in items:
            rule = catalog.get(f["rule_id"], {})
            blocks.append(
                f"### {f['id']}: {f['title']}\n\n"
                f"- Severidad: {SEV_ES[f['severity']]}. Certeza: {CONFIDENCE_LABEL[f['confidence']]}. Esfuerzo: {EFFORT_ES[f['effort']]}.\n"
                f"- Problema: {f['description']}\n"
                f"- Qué hacer: {f['recommendation']}\n\n"
                f"Evidencia:\n\n{_evidence_md(f)}\n"
            )
            acceptance.append(f"- `{f['id']}`: {rule.get('acceptance', 'La evidencia citada ya no existe y el comportamiento es correcto.')}")
            seen_rules.add(f["rule_id"])
        acceptance.append("- No se modificó ningún archivo fuera de Alcance.")
        acceptance.append("- Las pruebas existentes del repositorio, si las hay, siguen pasando.")

        text = tmpl.substitute(
            number=number, group=group, auditor_version=run["auditor"]["version"], run_id=run["run_id"],
            target_name=run["target"]["name"], revision=run["target"]["revision"],
            finding_ids=", ".join(f"`{f['id']}`" for f in items),
            conventions=conventions, scope=scope, findings_section="\n".join(blocks),
            acceptance="\n".join(acceptance),
        )
        fname = f"{number}-{_slug(group)}.md"
        (prompts_dir / fname).write_text(text, encoding="utf-8", newline="\n")
        index.append((fname, group, items))

    lines = ["# Índice de prompts de cambio", "",
             f"Run `{run['run_id']}`. Ejecutar en orden, uno por sesión y por commit, dentro del repositorio auditado.", "",
             "| # | Archivo | Grupo | Hallazgos | Severidad máxima |", "|---|---|---|---|---|"]
    for i, (fname, group, items) in enumerate(index, 1):
        lines.append(f"| {i} | [{fname}]({fname}) | {group} | {len(items)} | {SEV_ES[items[0]['severity']]} |")
    if not index:
        lines.append("| - | - | Sin hallazgos | 0 | - |")
    (prompts_dir / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return index


def _delta(run: dict, baseline: dict) -> str:
    cur = {f["id"]: f for f in run["findings"]}
    old = {f["id"]: f for f in baseline["findings"]}
    new = [cur[i] for i in cur if i not in old]
    persistent = [cur[i] for i in cur if i in old]
    resolved = [old[i] for i in old if i not in cur]
    rows = [f"## Comparación con la auditoría anterior (`{baseline['run_id']}`)", "",
            "| Estado | Cantidad |", "|---|---|",
            f"| Nuevos | {len(new)} |", f"| Persistentes | {len(persistent)} |", f"| Resueltos | {len(resolved)} |", ""]
    if baseline["target"]["revision"] == run["target"]["revision"]:
        rows += ["Aviso: ambas auditorías corresponden a la misma revisión; no hay cambios de código que comparar.", ""]
    for title, items in (("Nuevos", new), ("Resueltos", resolved)):
        if items:
            rows.append(f"**{title}:** " + ", ".join(f"`{f['id']}`" for f in _sorted_findings(items)))
            rows.append("")
    return "\n".join(rows) + "\n"


def render_report(run: dict, out_dir: Path, index: list, baseline: dict | None = None, root: Path = ROOT) -> Path:
    findings = run["findings"]
    counts = {s: sum(1 for f in findings if f["severity"] == s) for s in SEVERITIES}
    table = ["| Severidad | Hallazgos |", "|---|---|"] + [f"| {SEV_ES[s]} | {counts[s]} |" for s in SEVERITIES]
    table.append(f"| **Total** | **{len(findings)}** |")

    blocks = []
    for sev in SEVERITIES:
        group = [f for f in _sorted_findings(findings) if f["severity"] == sev]
        if not group:
            continue
        blocks.append(f"### {SEV_ES[sev]}\n")
        for f in group:
            blocks.append(
                f"#### {f['id']}: {f['title']}\n\n"
                f"- Regla: `{f['rule_id']}` v{f['rule_version']}. Certeza: {CONFIDENCE_LABEL[f['confidence']]}. "
                f"Esfuerzo: {EFFORT_ES[f['effort']]}. Detectado por: {f['detected_by']}. Grupo de cambio: `{f['change_group']}`.\n"
                f"- Descripción: {f['description']}\n"
                f"- Recomendación: {f['recommendation']}\n\n"
                f"Evidencia:\n\n{_evidence_md(f)}\n"
            )
    if not blocks:
        blocks.append("Sin hallazgos.\n")

    evaluated = sum(1 for r in run["rules"] if r["status"] == "evaluated")
    na = [r for r in run["rules"] if r["status"] == "not_applicable"]
    na_detail = ""
    if na:
        na_detail = "Reglas no aplicables:\n\n" + "\n".join(f"- `{r['id']}`: {r['note']}" for r in na) + "\n"
    domains = ", ".join(f"{k} ({v})" for k, v in run["coverage"]["files_by_domain"].items()) or "ninguno detectado"
    prompts_index = ("\n".join(f"{i}. [{fname}](prompts/{fname}): {group}, {len(items)} hallazgo(s)"
                               for i, (fname, group, items) in enumerate(index, 1))
                     or "No se generaron prompts: no hay hallazgos.")

    text = _template("informe.md.tmpl", root).substitute(
        target_name=run["target"]["name"], run_id=run["run_id"], revision=run["target"]["revision"],
        dirty_note=" (con cambios sin commitear)" if run["target"].get("dirty") else "",
        profile=f"{run['profile']['name']} v{run['profile']['version']}",
        auditor_version=run["auditor"]["version"], auditor_revision=run["auditor"]["revision"][:12],
        started_at=run["started_at"], finished_at=run.get("finished_at") or "-",
        executive_summary=run["executive_summary"].strip() or "(pendiente)",
        severity_table="\n".join(table), delta_section=_delta(run, baseline) if baseline else "",
        files_total=run["coverage"]["files_total"], domains=domains,
        rules_evaluated=evaluated, rules_na=len(na), rules_na_detail=na_detail,
        findings_section="\n".join(blocks),
        limitations="\n".join(f"- {normalize(l)}" for l in run["limitations"]) or "- Ninguna declarada.",
        prompts_index=prompts_index,
    )
    path = out_dir / "informe.md"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path
