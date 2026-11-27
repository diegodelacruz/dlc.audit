"""TRN-007 (evidencia file_size) y forma de out_of_scope_changes en el cierre."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from dlc_audit.closure import check_closure
from dlc_audit.render import render_integrator_prompt, render_prompts, render_report
from dlc_audit.scan import run_scan
from dlc_audit.validate import validate_run
from test_audit import build_target
from test_protocol import finish, git

BIG = 1_200_000


class LargeFileTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name)
        self.target = build_target(self.base)
        (self.target / "datos").mkdir()
        (self.target / "datos/volcado.dat").write_bytes(b"a" * BIG)
        git(self.target, "add", "-A")
        git(self.target, "commit", "-q", "-m", "datos")
        self.run_doc = run_scan(self.target)

    def trn007(self, run):
        return [f for f in run["findings"] if f["rule_id"] == "TRN-007"]

    def test_scan_emits_file_size_and_validates(self):
        found = self.trn007(self.run_doc)
        self.assertEqual(len(found), 1)
        ev = found[0]["evidence"][0]
        self.assertEqual((ev["type"], ev["path"], ev["size_bytes"]), ("file_size", "datos/volcado.dat", BIG))
        errors, _ = validate_run(copy.deepcopy(self.run_doc), self.target)
        self.assertEqual(errors, [])
        self.assertTrue(any("volcado.dat" in l for l in self.run_doc["limitations"]))
        run = finish(copy.deepcopy(self.run_doc), self.target)   # valida con final=True
        self.assertEqual(validate_run(run, self.target, final=True)[0], [])

    def test_finding_id_is_stable(self):
        again = run_scan(self.target)
        self.assertEqual(self.trn007(again)[0]["id"], self.trn007(self.run_doc)[0]["id"])

    def test_wrong_size_missing_size_and_missing_file_fail(self):
        for mutate, expected in (
            (lambda ev: ev.update(size_bytes=BIG + 1), "no coincide"),
            (lambda ev: ev.update(size_bytes="grande"), "entero"),
            (lambda ev: ev.pop("size_bytes"), "entero"),
            (lambda ev: ev.update(path="datos/no-existe.dat"), "no existe"),
        ):
            run = copy.deepcopy(self.run_doc)
            mutate(self.trn007(run)[0]["evidence"][0])
            errors, _ = validate_run(run, self.target)
            self.assertTrue(any(expected in e for e in errors), (expected, errors))

    def test_report_and_prompts_render(self):
        run = finish(copy.deepcopy(self.run_doc), self.target)
        out = self.base / "out"
        index = render_prompts(run, out)
        text = render_report(run, out, index).read_text(encoding="utf-8")
        self.assertIn("datos/volcado.dat", text)
        self.assertIn("1.2 MB (1200000 bytes)", text)
        prompts = "\n".join(p.read_text(encoding="utf-8") for p in (out / "prompts").glob("[0-9]*.md"))
        self.assertIn("1.2 MB (1200000 bytes)", prompts)
        integ = render_integrator_prompt(run, out).read_text(encoding="utf-8")
        self.assertIn("datos/volcado.dat", integ)


class OutOfScopeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name)
        self.repo = build_target(self.base)
        self.run_doc = run_scan(self.repo)
        (self.repo / "NOTAS.md").write_text("extra\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "extra")
        self.head = git(self.repo, "rev-parse", "HEAD")

    def closure(self, extra):
        run = self.run_doc
        findings = [{"id": f["id"], "status": "not_fixed", "note": "pendiente"} for f in run["findings"]]
        return {"run_id": run["run_id"], "base_revision": run["target"]["revision"], "head_revision": self.head,
                "branch": "main", "findings": findings, "out_of_scope_changes": extra}

    def check(self, extra):
        return check_closure(self.run_doc, self.closure(extra), self.repo)

    def drift(self, check):
        return [w for w in check["warnings"] if "deriva" in w]

    def test_without_declaration_there_is_drift(self):
        self.assertTrue(self.drift(self.check([])))

    def test_path_covers_drift(self):
        check = self.check([{"path": "NOTAS.md", "reason": "nota"}])
        self.assertEqual(check["errors"], [])
        self.assertEqual(self.drift(check), [])
        self.assertFalse(any("alias" in w for w in check["warnings"]))

    def test_file_alias_covers_drift_with_notice(self):
        check = self.check([{"file": "NOTAS.md", "commit": self.head, "reason": "nota"}])
        self.assertEqual(check["errors"], [])
        self.assertEqual(self.drift(check), [])
        self.assertTrue(any("alias" in w and "'file'" in w for w in check["warnings"]))

    def test_path_preferred_over_file(self):
        check = self.check([{"path": "NOTAS.md", "file": "otro.md", "reason": "x"}])
        self.assertEqual(self.drift(check), [])
        self.assertFalse(any("alias" in w for w in check["warnings"]))

    def test_malformed_entries_warn_without_raising(self):
        check = self.check(["NOTAS.md", {"reason": "sin ruta"}, {"path": 5, "reason": "x"},
                            {"path": "NOTAS.md"}, None])
        self.assertEqual(check["errors"], [])
        joined = " ".join(check["warnings"])
        self.assertIn("no es un objeto", joined)
        self.assertIn("no tiene 'path'", joined)
        self.assertIn("no tiene 'reason'", joined)
        self.assertEqual(self.drift(check), [])   # la entrada con path válido sí cubre

    def test_non_list_value_does_not_raise(self):
        cierre = self.closure([])
        cierre["out_of_scope_changes"] = None
        check_closure(self.run_doc, cierre, self.repo)

    def test_prompt_shows_exact_shape(self):
        run = finish(copy.deepcopy(self.run_doc), self.repo)
        text = render_integrator_prompt(run, self.base / "out").read_text(encoding="utf-8")
        self.assertIn('{"path": "<ruta relativa>", "reason": "<motivo>"}', text)
        self.assertIn("usa `path`, no `file`", text)


if __name__ == "__main__":
    unittest.main()
