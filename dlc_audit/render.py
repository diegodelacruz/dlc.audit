"""Genera informe.md y prompts de cambio desde el JSON del run."""
from __future__ import annotations

import re
import json
from pathlib import Path
from string import Template

from .requisitos import load_requirements
from .common import (
    CONFIDENCE_LABEL, ROOT, SEVERITIES, ensure_outside_repo, is_blocking, load_catalog, load_profile, normalize,
    verdict,
)

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
    out_dir = ensure_outside_repo(out_dir)
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
             f"Run `{run['run_id']}`. El integrador los ejecuta en este orden, dentro de una misma sesión, con un commit por prompt.", "",
             "| # | Archivo | Grupo | Hallazgos | Severidad máxima |", "|---|---|---|---|---|"]
    for i, (fname, group, items) in enumerate(index, 1):
        lines.append(f"| {i} | [{fname}]({fname}) | {group} | {len(items)} | {SEV_ES[items[0]['severity']]} |")
    if not index:
        lines.append("| - | - | Sin hallazgos | 0 | - |")
    (prompts_dir / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return index


def _conversation(profile: dict, role: str) -> tuple[str, str]:
    """(MISMA|NUEVA, motivo) para el rol indicado; configurable en el perfil (handoff)."""
    cfg = profile.get("handoff", {}).get(role, {"conversation": "NUEVA", "reason": "el prompt es autosuficiente"})
    return cfg["conversation"], cfg["reason"][0].upper() + cfg["reason"][1:] + "."


def render_integrator_prompt(run: dict, out_dir: Path, root: Path = ROOT) -> Path | None:
    """Prompt único para el integrador, con plantilla de cierre prellenada. None si no hay hallazgos."""
    findings = _sorted_findings(run["findings"])
    if not findings:
        return None
    out_dir = ensure_outside_repo(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    profile = load_profile(run["profile"]["name"], root)
    rows = ["| Id | Severidad | Certeza | Bloquea | Título | Archivos |", "|---|---|---|---|---|---|"]
    for f in findings:
        paths = ", ".join(f"`{p}`" for p in dict.fromkeys(e["path"] for e in f["evidence"]))
        rows.append(f"| `{f['id']}` | {SEV_ES[f['severity']]} | {CONFIDENCE_LABEL[f['confidence']]} | "
                    f"{'sí' if is_blocking(f, profile) else 'no'} | {f['title']} | {paths} |")
    entry = {"status": "<fixed|not_applicable|not_fixed|partial>", "commits": ["<sha>"], "files": ["<ruta>"],
             "verification": "<qué comprobaste y cómo>", "note": "<obligatorio si no es fixed>"}
    items = ",\n".join("    " + json.dumps({"id": f["id"], **entry}, ensure_ascii=False) for f in findings)
    closure_json = (
        "{\n"
        f'  "run_id": {json.dumps(run["run_id"])},\n'
        f'  "base_revision": {json.dumps(run["target"]["revision"])},\n'
        '  "head_revision": "<sha del último commit empujado>",\n'
        '  "branch": "<rama que auditará el auditor>",\n'
        f'  "findings": [\n{items}\n  ],\n'
        '  "out_of_scope_changes": []\n'
        "}"
    )
    conv_i, why_i = _conversation(profile, "integrator")
    conv_a, why_a = _conversation(profile, "auditor")
    text = _template("prompt-integrador.md.tmpl", root).substitute(
        round=run.get("round", 1), repo_url=run["target"].get("url") or run["target"]["name"],
        ref=run["target"].get("ref", "main"), revision=run["target"]["revision"],
        verdict=verdict(run["findings"], profile), n_total=len(findings),
        n_blocking=sum(1 for f in findings if is_blocking(f, profile)),
        summary_table="\n".join(rows), audit_branch=f"audit/{run['run_id']}", run_id=run["run_id"],
        short_run=run["run_id"].split("-")[0], closure_json=closure_json,
        conv_i=conv_i, why_i=why_i, conv_a=conv_a, why_a=why_a,
    )
    path = out_dir / "prompt-integrador.md"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


MERGE_COMMANDS = {
    "no-ff": ["git checkout {base}", "git pull --ff-only origin {base}",
              'git merge --no-ff origin/{branch} -m "Integra {branch} (auditoría aprobada {run})"'],
    "squash": ["git checkout {base}", "git pull --ff-only origin {base}", "git merge --squash origin/{branch}",
               'git commit -m "Integra {branch} (auditoría aprobada {run})"'],
    "ff-only": ["git checkout {base}", "git pull --ff-only origin {base}", "git merge --ff-only origin/{branch}"],
}


def render_merge_prompt(final_run: dict, branch: str, base: str, root: Path = ROOT) -> str | None:
    """Prompt para que el integrador integre la rama aprobada. None si no hay nada que integrar."""
    if branch == base:
        return None
    profile = load_profile(final_run["profile"]["name"], root)
    strategy = profile.get("merge", {}).get("strategy", "no-ff")
    if strategy not in MERGE_COMMANDS:
        raise ValueError(f"Estrategia de merge desconocida: {strategy}")
    fmt = {"base": base, "branch": branch, "run": final_run["run_id"]}
    indent = "   "
    merge_cmds = "\n".join(indent + c.format(**fmt) for c in MERGE_COMMANDS[strategy])
    cleanup = [
        f"{indent}git worktree list",
        f"{indent}# Por cada worktree cuya ruta sea ../audit-<sello>, resto de la auditoría:",
        f"{indent}git worktree remove --force <ruta>",
        f"{indent}git worktree prune",
        f"{indent}git branch --list \"audit/*\"",
        f"{indent}# Por cada rama local listada:",
        f"{indent}git branch -D <rama>",
        f"{indent}git fetch origin --prune",
    ]
    conv, why = _conversation(profile, "integrator")
    return _template("prompt-merge.md.tmpl", root).substitute(
        conv=conv, why=why, repo_url=final_run["target"].get("url") or final_run["target"]["name"],
        branch=branch, base=base, approved_sha=final_run["target"]["revision"],
        verdict=verdict(final_run["findings"], profile), final_run_id=final_run["run_id"],
        n_rounds=final_run.get("round", 1), strategy=strategy, merge_commands=merge_cmds,
        cleanup_commands="\n".join(cleanup),
        correction_branch_step=(f"Si creaste `{branch}` exclusivamente para esta auditoría y ya quedó integrada en `{base}`, "
                                f"elimínala (`git push origin --delete {branch}` y `git branch -d {branch}`). "
                                "Si no estás seguro de que sea exclusiva de esta auditoría, no la elimines y repórtalo."),
    )


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


def compliance_matrix(run: dict, catalog: dict, requirements: dict) -> list[tuple[str, dict, list[str], str]]:
    """Estado por requisito oficial: CUMPLE, NO_CUMPLE, NO_APLICA o NO_VERIFICADO (criterio C10)."""
    status = {r["id"]: r["status"] for r in run["rules"]}
    with_findings = {f["rule_id"] for f in run["findings"]}
    linked: dict[str, list[str]] = {}
    for rid in status:
        for req in catalog.get(rid, {}).get("requirements", []):
            linked.setdefault(req, []).append(rid)
    rows = []
    for req in sorted(linked):
        info = requirements.get(req)
        if info is None:
            continue
        rules = sorted(linked[req])
        states = [status[r] for r in rules]
        if not info["verified"]:
            estado = "NO_VERIFICADO"
        elif any(r in with_findings for r in rules):
            estado = "NO_CUMPLE"
        elif "pending" in states:
            estado = "NO_VERIFICADO"
        elif all(s == "not_applicable" for s in states):
            estado = "NO_APLICA"
        else:
            estado = "CUMPLE"
        rows.append((req, info, rules, estado))
    return rows


def _compliance_section(run: dict, catalog: dict, root: Path) -> str:
    rows = compliance_matrix(run, catalog, load_requirements(root))
    if not rows:
        return ""
    lines = ["## Cumplimiento de requisitos oficiales", "",
             "| Requisito | Descripción | Reglas | Estado |", "|---|---|---|---|"]
    for req, info, rules, estado in rows:
        title = info["title"].replace("|", "\\|")
        lines.append(f"| {req} | {title} | {', '.join(rules)} | {estado} |")
    lines += ["", "`CUMPLE` significa que las reglas vinculadas se evaluaron sin hallazgos; no sustituye la verificación "
              "humana. `NO_VERIFICADO` indica una regla pendiente o un requisito que la documentación oficial no permitió "
              "comprobar. Las citas literales de cada requisito están en `docs/cumplimiento/` de dlc.audit.", ""]
    return "\n".join(lines) + "\n"


def _closure_section(check: dict) -> str:
    rows = ["## Verificación del cierre del integrador", "",
            "| Declarado | Cantidad |", "|---|---|"]
    rows += [f"| {k} | {v} |" for k, v in check.get("claims", {}).items()]
    rows.append("")
    if check.get("contradicted"):
        rows.append("**Correcciones declaradas como `fixed` que la nueva auditoría sigue detectando:** "
                    + ", ".join(f"`{i}`" for i in check["contradicted"]))
        rows.append("")
    for title, key in (("Errores", "errors"), ("Advertencias (discrepancias y deriva)", "warnings")):
        if check.get(key):
            rows.append(f"**{title}:**")
            rows += [f"- {m}" for m in check[key]]
            rows.append("")
    return "\n".join(rows) + "\n"


def render_report(run: dict, out_dir: Path, index: list, baseline: dict | None = None, root: Path = ROOT,
                  closure: dict | None = None, has_integrator_prompt: bool = False) -> Path:
    out_dir = ensure_outside_repo(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    findings = run["findings"]
    profile = load_profile(run["profile"]["name"], root)
    dictamen = verdict(findings, profile)
    n_block = sum(1 for f in findings if is_blocking(f, profile))
    detail = {
        "APROBADO": "No hay hallazgos abiertos. No se requiere nueva ronda.",
        "APROBADO CON OBSERVACIONES": f"Hay {len(findings)} observación(es), ninguna bloqueante. Corregirlas es opcional.",
        "NO APROBADO": f"Hay {n_block} hallazgo(s) bloqueante(s) de {len(findings)}. Se requiere una nueva ronda tras corregirlos.",
    }[dictamen]
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
    lines = []
    if has_integrator_prompt:
        lines.append("- [prompt-integrador.md](prompt-integrador.md): prompt único para el integrador (incluye la plantilla de cierre).")
    lines += [f"- [prompts/{fname}](prompts/{fname}): {group}, {len(items)} hallazgo(s)"
              for fname, group, items in index]
    prompts_index = "\n".join(lines) or "No se generaron entregables: no hay hallazgos."

    text = _template("informe.md.tmpl", root).substitute(
        target_name=run["target"]["name"], run_id=run["run_id"], revision=run["target"]["revision"],
        dirty_note=" (con cambios sin commitear)" if run["target"].get("dirty") else "",
        profile=f"{run['profile']['name']} v{run['profile']['version']}",
        auditor_version=run["auditor"]["version"], auditor_revision=run["auditor"]["revision"][:12],
        round=run.get("round", 1),
        baseline_note=f" (baseline `{run['baseline_run_id']}`)" if run.get("baseline_run_id") else "",
        verdict=dictamen, verdict_detail=detail,
        closure_section=_closure_section(closure) if closure else "",
        compliance_section=_compliance_section(run, load_catalog(profile, root), root),
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
