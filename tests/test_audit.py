"""Pruebas de extremo a extremo: scan -> validate -> render sobre un objetivo sintético."""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from dlc_audit.common import finding_id, load_catalog, load_profile
from dlc_audit.render import render_prompts, render_report
from dlc_audit.scan import mask_sql, parse_frontmatter, run_scan
from dlc_audit.validate import validate_run

SQL_BAD = (
    "CREATE OR REPLACE PROCEDURE p_demo IS\n"
    "begin\n"
    "  select a,\n"
    "         b\n"
    "    from t\n"
    "   where x = 1;\n"
    "  execute immediate 'delete from ' || v_tabla;\n"
    "exception\n"
    "\twhen others then null;\n"
    "end;\n"
    "/\n"
)

PY_BAD = (
    "import subprocess\n"
    "def f(cur, name):\n"
    "    cur.execute(f\"select * from t where n = '{name}'\")\n"
    "    try:\n"
    "        pass\n"
    "    except:\n"
    "        pass\n"
    "    subprocess.run('ls', shell=True)\n"
    "    path = '" + "s3://" + "bucket-fijo/datos'\n"
)


def build_target(base: Path) -> Path:
    t = base / "objetivo"
    (t / ".claude/skills/Mala_Skill").mkdir(parents=True)
    (t / ".claude/agents").mkdir(parents=True)
    (t / "sql").mkdir()
    (t / "src").mkdir()
    (t / ".claude/skills/Mala_Skill/SKILL.md").write_text(
        "---\nname: Mala_Skill\n---\nVer [guia](refs/no-existe.md) y [web](https://example.com).\n", encoding="utf-8")
    (t / ".claude/agents/ag.md").write_text("---\nname: ag\ndescription: agente de prueba\n---\ncuerpo\n", encoding="utf-8")
    (t / ".claude/settings.json").write_text(json.dumps({"permissions": {"allow": ["Bash(*)"]}}, indent=2), encoding="utf-8")
    (t / "sql/p_demo.sql").write_text(SQL_BAD, encoding="utf-8")
    (t / "src/app.py").write_text(PY_BAD, encoding="utf-8")
    (t / "requirements.txt").write_text("fastapi\nuvicorn==0.30.0\n", encoding="utf-8")
    # El secreto se arma en tiempo de ejecucion para no versionar valores con forma de credencial.
    fake = "AKIA" + "ABCDEFGHIJKLMNOP"
    (t / "src/conf.py").write_text(f"KEY = '{fake}'\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(t)], check=True)
    subprocess.run(["git", "-C", str(t), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(t), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x"], check=True)
    return t


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.base = Path(cls._tmp.name)
        cls.target = build_target(cls.base)
        cls.run_doc = run_scan(cls.target)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def rule_ids(self):
        return {f["rule_id"] for f in self.run_doc["findings"]}

    def test_catalog_is_consistent(self):
        catalog = load_catalog(load_profile("default"))
        self.assertGreaterEqual(len(catalog), 30)
        from dlc_audit.scan import DETECTORS
        for rule in catalog.values():
            self.assertIn(rule["method"], ("deterministic", "judgment"))
            if rule["method"] == "deterministic":
                self.assertIn(rule["detector"], DETECTORS, rule["id"])
            for key in ("remediation", "acceptance", "valid_from", "version"):
                self.assertTrue(rule.get(key), f"{rule['id']} sin {key}")

    def test_detectors_find_expected_rules(self):
        expected = {"TRN-001", "TRN-003", "TRN-004", "TRN-006", "SKL-001", "SKL-002", "SKL-006",
                    "SKL-008", "SKL-010", "SQL-001", "SQL-002", "SQL-003", "SQL-004", "SQL-006",
                    "SQL-007", "PYT-001", "PYT-002", "PYT-004", "PYT-005", "PYT-007"}
        missing = expected - self.rule_ids()
        self.assertFalse(missing, f"No detectadas: {missing}")

    def test_judgment_rules_are_pending(self):
        pending = {r["id"] for r in self.run_doc["rules"] if r["status"] == "pending"}
        self.assertTrue({"SKL-003", "SQL-005", "PYT-003", "TRN-005"} <= pending)

    def test_secret_is_redacted(self):
        blob = json.dumps(self.run_doc)
        self.assertNotIn("ABCDEFGHIJKLMNOP", blob)
        sec = next(f for f in self.run_doc["findings"] if f["rule_id"] == "TRN-001")
        self.assertTrue(sec["evidence"][0]["redacted"])

    def test_scan_does_not_modify_target(self):
        status = subprocess.run(["git", "-C", str(self.target), "status", "--porcelain"],
                                capture_output=True, text=True, check=True).stdout
        self.assertEqual(status, "")

    def test_scan_is_idempotent(self):
        again = run_scan(self.target)
        self.assertEqual({f["id"] for f in again["findings"]}, {f["id"] for f in self.run_doc["findings"]})

    def test_validate_passes_for_scan_output_until_final(self):
        errors, warnings = validate_run(copy.deepcopy(self.run_doc), self.target)
        self.assertEqual(errors, [])
        self.assertTrue(any("pendiente" in w for w in warnings))

    def test_final_requires_no_pending_and_summary(self):
        errors, _ = validate_run(copy.deepcopy(self.run_doc), self.target, final=True)
        self.assertTrue(any("pendiente" in e for e in errors))
        self.assertTrue(any("executive_summary" in e for e in errors))

    def test_validate_rejects_fabricated_evidence(self):
        run = copy.deepcopy(self.run_doc)
        f = next(x for x in run["findings"] if x["rule_id"] == "SQL-007")
        f["evidence"][0]["excerpt"] = "esto no esta en el archivo"
        errors, _ = validate_run(run, self.target)
        self.assertTrue(any("extracto no coincide" in e for e in errors))

    def test_validate_rejects_missing_file_and_bad_lines(self):
        run = copy.deepcopy(self.run_doc)
        f = next(x for x in run["findings"] if x["rule_id"] == "SQL-007")
        f["evidence"][0]["path"] = "sql/inexistente.sql"
        errors, _ = validate_run(run, self.target)
        self.assertTrue(any("no existe" in e for e in errors))

    def test_validate_rejects_false_absence_and_path_escape(self):
        run = copy.deepcopy(self.run_doc)
        f = next(x for x in run["findings"] if x["rule_id"] == "TRN-003")
        f["evidence"][0]["path"] = "requirements.txt"
        errors, _ = validate_run(run, self.target)
        self.assertTrue(any("ausencia" in e for e in errors))
        f["evidence"][0]["path"] = "../fuera.txt"
        errors, _ = validate_run(run, self.target)
        self.assertTrue(any("relativo" in e for e in errors))

    def test_agent_finding_id_assignment_and_duplicates(self):
        run = copy.deepcopy(self.run_doc)
        base = next(x for x in run["findings"] if x["rule_id"] == "SQL-007")
        agent = copy.deepcopy(base)
        agent.pop("id")
        agent["detected_by"] = "agent"
        agent["confidence"] = "inferential"
        run["findings"].append(agent)
        errors, _ = validate_run(run, self.target)
        self.assertTrue(any("falta 'id'" in e for e in errors))
        errors, _ = validate_run(run, self.target, assign_ids=True)
        self.assertTrue(any("duplicado" in e for e in errors))

    def test_finding_id_ignores_line_numbers(self):
        ev = [{"type": "file", "path": "a.sql", "line_start": 3, "line_end": 3, "excerpt": "when  others\nthen null;"}]
        ev2 = [dict(ev[0], line_start=40, line_end=41, excerpt="when others then null;")]
        self.assertEqual(finding_id("SQL-007", ev), finding_id("SQL-007", ev2))

    def test_full_pipeline_renders(self):
        run = copy.deepcopy(self.run_doc)
        for r in run["rules"]:
            if r["status"] == "pending":
                r["status"] = "not_applicable"
                r["note"] = "Evaluada en la prueba."
        run["executive_summary"] = "Resumen de prueba."
        run["finished_at"] = "2026-11-26T00:00:00Z"
        errors, _ = validate_run(run, self.target, final=True)
        self.assertEqual(errors, [])
        out = self.base / "out"
        index = render_prompts(run, out)
        report = render_report(run, out, index, baseline=copy.deepcopy(run))
        text = report.read_text(encoding="utf-8")
        self.assertIn("Resumen de prueba.", text)
        self.assertIn("Comparación con la auditoría anterior", text)
        self.assertNotIn("ABCDEFGHIJKLMNOP", text)
        self.assertTrue((out / "prompts/INDEX.md").is_file())
        first = sorted((out / "prompts").glob("0*.md"))[0].read_text(encoding="utf-8")
        self.assertIn("Criterios de aceptación", first)
        self.assertNotIn("ABCDEFGHIJKLMNOP", first)

    def test_helpers(self):
        self.assertEqual(mask_sql("select 'a,b' -- c\nfrom t"), "select       " + " " * 4 + "\nfrom t")
        fm = parse_frontmatter("---\nname: x\ndescription: >\n  uno\n  dos\n---\n")
        self.assertEqual(fm, {"name": "x", "description": "uno dos"})
        self.assertIsNone(parse_frontmatter("sin frontmatter"))


if __name__ == "__main__":
    unittest.main()


class AcceptedExceptionsTests(unittest.TestCase):
    def test_covered_findings_are_dropped_and_declared(self):
        from dlc_audit.scan import apply_exceptions, active_exceptions
        exc = {"id": "EXC-T", "repo": "objetivo", "rule_id": "TRN-007", "paths": ["fx/*.zip"],
               "reason": "fixture", "approved_by": "t", "valid_from": "2026-01-01", "valid_to": None}
        mk = lambda rule, path: {"rule_id": rule, "evidence": [{"path": path}]}
        findings = [mk("TRN-007", "fx/a.zip"), mk("TRN-007", "otro/b.zip"), mk("TRN-001", "fx/c.zip")]
        kept, used = apply_exceptions(findings, [exc])
        self.assertEqual([f["evidence"][0]["path"] for f in kept], ["otro/b.zip", "fx/c.zip"])
        self.assertEqual(used[0]["paths"], ["fx/a.zip"])
        profile = {"accepted_exceptions": [exc]}
        self.assertEqual(len(active_exceptions(profile, "objetivo", "2026-11-26")), 1)
        self.assertEqual(active_exceptions(profile, "otro", "2026-11-26"), [])
        self.assertEqual(active_exceptions(profile, "objetivo", "2025-12-31"), [])
        exc["valid_to"] = "2026-06-30"
        self.assertEqual(active_exceptions(profile, "objetivo", "2026-11-26"), [])
