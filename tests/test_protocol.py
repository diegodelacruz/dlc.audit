"""Protocolo auditor-integrador en dos rondas, con un remoto git local."""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from dlc_audit.closure import check_closure, cross_check
from dlc_audit.common import save_json, load_profile, sanitize_url, verdict
from dlc_audit.gitops import GitError, fetch, publish, safe_source
from dlc_audit.render import render_integrator_prompt, render_prompts, render_report
from dlc_audit.scan import run_scan
from dlc_audit.validate import validate_run
from test_audit import build_target


def git(path: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def finish(run: dict, target: Path) -> dict:
    """Simula la evaluación del agente: cierra reglas de juicio y completa el resumen."""
    for r in run["rules"]:
        if r["status"] == "pending":
            r["status"], r["note"] = "not_applicable", "Evaluada en la prueba."
    run["executive_summary"] = "Resumen de prueba."
    run["finished_at"] = "2026-11-26T00:00:00Z"
    errors, _ = validate_run(run, target, final=True)
    assert errors == [], errors
    return run


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.base = Path(cls._tmp.name)
        src = build_target(cls.base)                      # repositorio del integrador
        git(src, "branch", "-M", "main")
        cls.remote = cls.base / "origin.git"
        subprocess.run(["git", "clone", "-q", "--bare", str(src), str(cls.remote)], check=True)
        git(src, "remote", "add", "origin", str(cls.remote))
        git(src, "fetch", "-q", "origin")
        git(src, "branch", "-u", "origin/main", "main")
        cls.src = src
        cls.work = cls.base / "work"

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    # --- ronda 1 ---------------------------------------------------------
    def round1(self) -> tuple[dict, Path]:
        info = fetch(str(self.remote), self.work, "main")
        run = run_scan(Path(info["path"]), ref="main")
        run = finish(run, Path(info["path"]))
        run_path = self.base / "audits1" / "hallazgos.json"
        save_json(run_path, run)
        index = render_prompts(run, run_path.parent)
        prompt = render_integrator_prompt(run, run_path.parent)
        render_report(run, run_path.parent, index, has_integrator_prompt=True)
        self.assertIsNotNone(prompt)
        return run, run_path

    def test_01_safe_source_and_sanitize(self):
        self.assertFalse(safe_source("--upload-pack=touch /tmp/x"))
        self.assertFalse(safe_source("no-es-un-repo"))
        self.assertTrue(safe_source("https://github.com/a/b.git"))
        self.assertEqual(sanitize_url("https://u:tok@github.com/a/b.git"), "https://github.com/a/b.git")

    def test_02_fetch_and_scan_record_url_ref_round(self):
        info = fetch(str(self.remote), self.work, "main")
        run = run_scan(Path(info["path"]), ref="main")
        self.assertEqual(run["round"], 1)
        self.assertEqual(run["target"]["ref"], "main")
        self.assertEqual(run["target"]["revision"], info["revision"])
        self.assertTrue(run["target"]["url"])

    def test_03_integrator_prompt_is_self_sufficient(self):
        run, run_path = self.round1()
        text = (run_path.parent / "prompt-integrador.md").read_text(encoding="utf-8")
        for needle in (run["target"]["revision"], f"audit/{run['run_id']}", run["run_id"],
                       "CONVERSACIÓN: MISMA", "NO APROBADO", "git worktree add", "cierre", "TRN-001"):
            self.assertIn(needle, text)
        self.assertNotIn("<" + "undefined", text)
        self.assertNotIn("ABCDEFGHIJKLMNOP", text)
        # La plantilla de cierre trae un id por hallazgo para que el integrador no omita ninguno.
        for f in run["findings"]:
            self.assertIn(f["id"], text)
        report = (run_path.parent / "informe.md").read_text(encoding="utf-8")
        self.assertIn("Dictamen: NO APROBADO", report)

    def test_04_publish_only_touches_audit_dir_and_never_twice(self):
        run, run_path = self.round1()
        res = publish(run_path, push=False)
        self.assertFalse(res["pushed"])
        self.assertTrue(all(f.startswith(f".audit/{run['run_id']}/") for f in res["files"]))
        res = publish(run_path, push=True)
        self.assertTrue(res["pushed"])
        heads = subprocess.run(["git", "ls-remote", "--heads", str(self.remote)], capture_output=True, text=True).stdout
        self.assertIn(f"refs/heads/audit/{run['run_id']}", heads)
        # La rama auditada no cambió y la rama de auditoría solo añade .audit/
        diff = git(self.remote, "diff", "--name-only", run["target"]["revision"], f"audit/{run['run_id']}").split()
        self.assertTrue(diff and all(d.startswith(".audit/") for d in diff))
        self.assertEqual(git(self.remote, "rev-parse", "main"), run["target"]["revision"])
        published = json.loads(git(self.remote, "show", f"audit/{run['run_id']}:.audit/{run['run_id']}/hallazgos.json"))
        self.assertEqual(published["target"]["path"], "(local)")
        self.assertNotIn(str(self.work), json.dumps(published))
        with self.assertRaises(GitError):
            publish(run_path, push=True)

    def test_05_publish_refuses_unfinished_run(self):
        info = fetch(str(self.remote), self.work, "main")
        run = run_scan(Path(info["path"]), ref="main")
        path = self.base / "audits_draft" / "hallazgos.json"
        save_json(path, run)
        with self.assertRaises(GitError):
            publish(path, push=False)

    # --- ronda 2 ---------------------------------------------------------
    def test_06_closure_and_second_round(self):
        run, run_path = self.round1()
        profile = load_profile("default")
        self.assertEqual(verdict(run["findings"], profile), "NO APROBADO")
        base_rev = run["target"]["revision"]

        # El integrador corrige SQL-007, toca un archivo no declarado y marca TRN-001 como corregido sin tocarlo.
        sql = self.src / "sql/p_demo.sql"
        sql.write_text(sql.read_text().replace("when others then null;", "when others then raise;"), encoding="utf-8")
        (self.src / "NOTAS.md").write_text("extra\n", encoding="utf-8")
        git(self.src, "add", "-A")
        git(self.src, "commit", "-q", "-m", "fix SQL-007")
        head = git(self.src, "rev-parse", "HEAD")
        git(self.src, "push", "-q", "origin", "main")

        findings = []
        for f in run["findings"]:
            if f["rule_id"] == "SQL-007":
                findings.append({"id": f["id"], "status": "fixed", "commits": [head], "files": ["sql/p_demo.sql"],
                                 "verification": "revisado"})
            elif f["rule_id"] == "TRN-001":
                findings.append({"id": f["id"], "status": "fixed", "commits": [head], "files": ["src/conf.py"],
                                 "verification": "dice que si"})
            else:
                findings.append({"id": f["id"], "status": "not_fixed", "note": "pendiente"})
        cierre = {"run_id": run["run_id"], "base_revision": base_rev, "head_revision": head,
                  "branch": "main", "findings": findings, "out_of_scope_changes": []}

        info = fetch(str(self.remote), self.work, "main")
        self.assertEqual(info["revision"], head)
        repo = Path(info["path"])
        check = check_closure(run, cierre, repo)
        self.assertEqual(check["errors"], [])
        self.assertTrue(any("NOTAS.md" in w and "deriva" in w for w in check["warnings"]))
        self.assertTrue(any("src/conf.py" in w and "no figura en el diff" in w for w in check["warnings"]))

        run2 = finish(run_scan(repo, ref="main", baseline=run), repo)
        self.assertEqual(run2["round"], 2)
        self.assertEqual(run2["baseline_run_id"], run["run_id"])
        ids2 = {f["id"] for f in run2["findings"]}
        sql007 = next(f["id"] for f in run["findings"] if f["rule_id"] == "SQL-007")
        trn001 = next(f["id"] for f in run["findings"] if f["rule_id"] == "TRN-001")
        self.assertNotIn(sql007, ids2)           # corregido de verdad
        self.assertIn(trn001, ids2)              # declarado corregido pero sigue ahí
        check = cross_check(check, cierre, run2)
        self.assertEqual(check["contradicted"], [trn001])

        out = self.base / "audits2"
        save_json(out / "hallazgos.json", run2)
        index = render_prompts(run2, out)
        render_integrator_prompt(run2, out)
        report = render_report(run2, out, index, baseline=run, closure=check, has_integrator_prompt=True)
        text = report.read_text(encoding="utf-8")
        self.assertIn("Verificación del cierre del integrador", text)
        self.assertIn(trn001, text)
        self.assertIn("Resueltos", text)

    def test_07_closure_structural_errors(self):
        run, _ = self.round1()
        repo = Path(fetch(str(self.remote), self.work, "main")["path"])
        head = git(repo, "rev-parse", "HEAD")
        ids = [f["id"] for f in run["findings"]]
        cierre = {"run_id": run["run_id"], "base_revision": run["target"]["revision"], "head_revision": head,
                  "branch": "main",
                  "findings": [{"id": ids[0], "status": "fixed", "commits": [], "files": []},
                               {"id": ids[0], "status": "not_fixed"},
                               {"id": "XXX-000", "status": "fixed"}]}
        check = check_closure(run, cierre, repo)
        joined = " ".join(check["errors"])
        self.assertIn("sin commits", joined)
        self.assertIn("más de una vez", joined)
        self.assertIn("no existe en el baseline", joined)
        self.assertIn("falta el hallazgo", joined)
        cierre["head_revision"] = "0" * 40
        self.assertTrue(any("no existe en el repositorio" in e for e in check_closure(run, cierre, repo)["errors"]))

    def test_08_approved_run_has_no_integrator_prompt(self):
        run, _ = self.round1()
        clean = copy.deepcopy(run)
        clean["findings"] = []
        out = self.base / "clean"
        out.mkdir()
        self.assertIsNone(render_integrator_prompt(clean, out))
        index = render_prompts(clean, out)
        text = render_report(clean, out, index, has_integrator_prompt=False).read_text(encoding="utf-8")
        self.assertIn("Dictamen: APROBADO", text)

    def test_09_verdict_rules(self):
        profile = load_profile("default")
        low = {"severity": "low", "confidence": "verified"}
        unv = {"severity": "high", "confidence": "unverified"}
        high = {"severity": "high", "confidence": "inferential"}
        self.assertEqual(verdict([low], profile), "APROBADO CON OBSERVACIONES")
        self.assertEqual(verdict([unv], profile), "APROBADO CON OBSERVACIONES")
        self.assertEqual(verdict([low, high], profile), "NO APROBADO")


if __name__ == "__main__":
    unittest.main()
