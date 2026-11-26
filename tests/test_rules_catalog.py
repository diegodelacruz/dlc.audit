"""Bloque 4: catálogo enlazado con docs/cumplimiento/, detectores nuevos y matriz de cumplimiento."""
from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from dlc_audit.common import ROOT, load_catalog, load_profile
from dlc_audit.render import compliance_matrix, render_report
from dlc_audit.requisitos import load_requirements
from dlc_audit.scan import run_scan
from dlc_audit.validate import validate_run
from test_audit import build_target
from test_protocol import finish

GOOD_SKILL = "---\nname: buena-skill\ndescription: Hace algo y se usa cuando el usuario lo pide.\n---\ncuerpo\n"


def make_repo(base: Path, files: dict[str, str]) -> Path:
    root = base / "objetivo"
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def rule_ids(run: dict) -> set[str]:
    return {f["rule_id"] for f in run["findings"]}


class CatalogTraceabilityTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog(load_profile("default"))
        self.reqs = load_requirements()

    def test_every_linked_requirement_exists_and_is_verified(self):
        for rule in self.catalog.values():
            for req in rule.get("requirements", []):
                self.assertIn(req, self.reqs, f"{rule['id']} cita {req}, que no existe en docs/cumplimiento/")
                self.assertTrue(self.reqs[req]["verified"], f"{rule['id']} cita {req}, que no está verificado")

    def test_verified_rules_with_an_external_source_are_linked_to_requirements(self):
        for rule in self.catalog.values():
            external = "docs/cumplimiento" in rule["source"]
            if external:
                self.assertTrue(rule.get("requirements"), f"{rule['id']} cita docs/cumplimiento sin requisitos")
            if rule["source_verified"] and rule["source"] != "convencion-interna" and not rule["source"].startswith("criterio C"):
                self.assertTrue(external, f"{rule['id']} está verificada pero no apunta a docs/cumplimiento/")

    def test_readme_rule_count_matches_the_catalog(self):
        m = re.search(r"\((\d+) reglas\)", (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIsNotNone(m)
        self.assertEqual(int(m.group(1)), len(self.catalog))

    def test_new_rules_exist_with_the_expected_method(self):
        for rid, method in (("SKL-013", "deterministic"), ("SKL-014", "deterministic"), ("SKL-015", "deterministic"),
                            ("SKL-016", "deterministic"), ("TRN-008", "judgment"), ("TRN-009", "judgment")):
            self.assertEqual(self.catalog[rid]["method"], method)


class SkillDetectorTests(unittest.TestCase):
    def scan(self, files: dict[str, str]) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(Path(tmp), files)
            run = run_scan(repo)
            errors, _ = validate_run(run, repo)
            self.assertEqual(errors, [])  # la evidencia de cada hallazgo es verificable en el archivo
            return run

    def test_reserved_words_xml_tags_and_extra_fields_are_detected(self):
        bad = ("---\nname: mi-claude-skill\ndescription: Usa <run_id> para algo.\nargument-hint: <x>\n---\ncuerpo\n")
        run = self.scan({".claude/skills/mi-claude-skill/SKILL.md": bad})
        self.assertTrue({"SKL-013", "SKL-014", "SKL-015"} <= rule_ids(run))

    def test_reserved_literal_names_are_detected(self):
        for name in ("synced", "anthropic-skills"):
            skill = f"---\nname: {name}\ndescription: Hace algo y se usa cuando se pide.\n---\ncuerpo\n"
            self.assertIn("SKL-013", rule_ids(self.scan({f".claude/skills/{name}/SKILL.md": skill})), name)

    def test_a_clean_skill_has_no_skill_findings(self):
        run = self.scan({".claude/skills/buena-skill/SKILL.md": GOOD_SKILL})
        self.assertEqual({r for r in rule_ids(run) if r.startswith("SKL")}, set())

    def test_agents_may_use_their_own_fields(self):
        agent = "---\nname: ag\ndescription: agente\ntools: Read\nmodel: inherit\n---\ncuerpo\n"
        run = self.scan({".claude/agents/ag.md": agent})
        self.assertNotIn("SKL-015", rule_ids(run))

    def test_spec_optional_fields_are_allowed(self):
        skill = ("---\nname: buena-skill\ndescription: Hace algo y se usa cuando se pide.\nlicense: MIT\n"
                 "compatibility: Requiere Python\nallowed-tools: Read\n---\ncuerpo\n")
        self.assertNotIn("SKL-015", rule_ids(self.scan({".agents/skills/buena-skill/SKILL.md": skill})))

    def test_unrestricted_bash_is_flagged_but_only_the_verified_forms(self):
        def settings(allow):
            return json.dumps({"permissions": {"allow": allow}})
        for form in ("Bash", "Bash(*)"):
            self.assertIn("SKL-008", rule_ids(self.scan({".claude/settings.json": settings([form])})), form)
        for fine in ("Bash(npm run test *)", "Read", "Bash(*:*)"):
            self.assertNotIn("SKL-008", rule_ids(self.scan({".claude/settings.json": settings([fine])})), fine)

    def test_bypass_permissions_in_project_settings_is_a_minor_finding_not_skl008(self):
        cfg = json.dumps({"permissions": {"defaultMode": "bypassPermissions"}})
        run = self.scan({".claude/settings.json": cfg})
        self.assertIn("SKL-016", rule_ids(run))
        self.assertNotIn("SKL-008", rule_ids(run))
        sev = next(f["severity"] for f in run["findings"] if f["rule_id"] == "SKL-016")
        self.assertEqual(sev, "low")
        other = json.dumps({"permissions": {"defaultMode": "default"}})
        self.assertNotIn("SKL-016", rule_ids(self.scan({".claude/settings.json": other})))


class ComplianceMatrixTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog(load_profile("default"))
        self.reqs = load_requirements()

    def matrix(self, statuses: dict[str, str], findings: list[str] | None = None, reqs=None) -> dict[str, str]:
        run = {"rules": [{"id": k, "status": v} for k, v in statuses.items()],
               "findings": [{"rule_id": r} for r in (findings or [])]}
        return {req: estado for req, _, _, estado in compliance_matrix(run, self.catalog, reqs or self.reqs)}

    def test_states(self):
        m = self.matrix({"SKL-003": "pending", "SKL-004": "evaluated", "SKL-009": "not_applicable"})
        self.assertEqual(m["S-03"], "NO_VERIFICADO")    # una regla vinculada sigue pendiente
        self.assertEqual(m["S-06"], "NO_APLICA")        # todas sus reglas son no aplicables
        m = self.matrix({"SKL-003": "evaluated", "SKL-004": "evaluated"})
        self.assertEqual(m["S-03"], "CUMPLE")
        m = self.matrix({"SKL-003": "evaluated", "SKL-004": "evaluated"}, findings=["SKL-004"])
        self.assertEqual(m["S-03"], "NO_CUMPLE")
        self.assertEqual(m["A-03"], "NO_CUMPLE")

    def test_a_requirement_not_verified_in_the_docs_is_never_reported_as_met(self):
        reqs = {k: dict(v) for k, v in self.reqs.items()}
        reqs["S-03"]["verified"] = False
        m = self.matrix({"SKL-003": "evaluated", "SKL-004": "evaluated"}, reqs=reqs)
        self.assertEqual(m["S-03"], "NO_VERIFICADO")

    def test_report_contains_the_section_with_real_states(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = build_target(Path(tmp))
            run = finish(run_scan(target), target)
            out = Path(tmp) / "out"
            text = render_report(run, out, [], has_integrator_prompt=False).read_text(encoding="utf-8")
        self.assertIn("## Cumplimiento de requisitos oficiales", text)
        self.assertRegex(text, r"\| S-01 \| .* \| SKL-001 .*\| NO_CUMPLE \|")   # la fixture tiene una skill sin description
        self.assertIn("no sustituye la verificación humana", text)


if __name__ == "__main__":
    unittest.main()
