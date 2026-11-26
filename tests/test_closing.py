"""Cierre del ciclo: archivado, borrado de ramas audit/* y prompt de merge."""
from __future__ import annotations

import copy
import subprocess
import tempfile
import unittest
from pathlib import Path

from dlc_audit.common import save_json
from dlc_audit.gitops import GitError, cleanup, default_branch, fetch, publish
from dlc_audit.render import render_merge_prompt, render_prompts, render_report, render_integrator_prompt
from dlc_audit.scan import run_scan
from test_audit import build_target
from test_protocol import finish, git


def heads(remote: Path) -> set[str]:
    out = subprocess.run(["git", "-C", str(remote), "for-each-ref", "--format=%(refname:short)", "refs/heads/"],
                         capture_output=True, text=True, check=True).stdout.split()
    return set(out)


class ClosingTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        src = build_target(self.base)
        git(src, "branch", "-M", "main")
        self.remote = self.base / "origin.git"
        subprocess.run(["git", "clone", "-q", "--bare", str(src), str(self.remote)], check=True)
        git(src, "remote", "add", "origin", str(self.remote))
        git(src, "fetch", "-q", "origin")
        self.src, self.work = src, self.base / "work"

        # Ronda 1
        info = fetch(str(self.remote), self.work, "main")
        run1 = finish(run_scan(Path(info["path"]), ref="main"), Path(info["path"]))
        self.publish_run(run1, self.base / "r1")
        self.run1 = run1

        # El integrador corrige en una rama propia
        git(src, "checkout", "-q", "-b", "fix/auditoria")
        (src / "NOTAS.md").write_text("corregido\n", encoding="utf-8")
        git(src, "add", "-A")
        git(src, "commit", "-q", "-m", "fix")
        git(src, "push", "-q", "origin", "fix/auditoria")
        self.head = git(src, "rev-parse", "HEAD")

        # Ronda 2
        info = fetch(str(self.remote), self.work, "fix/auditoria")
        self.repo = Path(info["path"])
        run2 = finish(run_scan(self.repo, ref="fix/auditoria", baseline=run1), self.repo)
        self.publish_run(run2, self.base / "r2")
        self.run2 = run2

        # Ronda 3: sin hallazgos (aprobada)
        run3 = copy.deepcopy(run2)
        run3.update(run_id="20261126T0600Z-origin", round=3, baseline_run_id=run2["run_id"], findings=[])
        self.run3 = finish(run3, self.repo)

        # Rama ajena al ciclo
        git(src, "checkout", "-q", "main")
        git(src, "checkout", "-q", "-b", "audit/20260101T0000Z-origin")
        (src / ".audit").mkdir(exist_ok=True)
        (src / ".audit/x.txt").write_text("otro ciclo\n", encoding="utf-8")
        git(src, "add", "-A")
        git(src, "commit", "-q", "-m", "otro ciclo")
        git(src, "push", "-q", "origin", "audit/20260101T0000Z-origin")
        git(src, "checkout", "-q", "main")
        fetch(str(self.remote), self.work, "fix/auditoria")
        self.archive = self.base / "archive"

    def publish_run(self, run: dict, out: Path) -> None:
        save_json(out / "hallazgos.json", run)
        index = render_prompts(run, out)
        render_integrator_prompt(run, out)
        render_report(run, out, index, has_integrator_prompt=True)
        publish(out / "hallazgos.json", push=True)

    def test_dry_run_archives_but_deletes_nothing(self):
        before = heads(self.remote)
        rep = cleanup(self.repo, self.run3, self.archive, delete=False)
        self.assertTrue(rep["dry_run"])
        self.assertEqual(sorted(rep["kept"]), sorted([f"audit/{self.run1['run_id']}", f"audit/{self.run2['run_id']}"]))
        self.assertEqual(heads(self.remote), before)
        self.assertTrue((self.archive / self.run1["run_id"] / "hallazgos.json").is_file())
        self.assertTrue((self.archive / self.run2["run_id"] / "informe.md").is_file())

    def test_delete_removes_only_cycle_branches(self):
        main_before = git(self.remote, "rev-parse", "main")
        fix_before = git(self.remote, "rev-parse", "fix/auditoria")
        rep = cleanup(self.repo, self.run3, self.archive, delete=True)
        self.assertEqual(len(rep["deleted"]), 2)
        remaining = heads(self.remote)
        self.assertEqual(remaining, {"main", "fix/auditoria", "audit/20260101T0000Z-origin"})
        self.assertIn("audit/20260101T0000Z-origin", rep["not_in_cycle"])
        self.assertEqual(git(self.remote, "rev-parse", "main"), main_before)
        self.assertEqual(git(self.remote, "rev-parse", "fix/auditoria"), fix_before)
        # El registro sobrevive al borrado
        self.assertTrue((self.archive / self.run1["run_id"] / "hallazgos.json").is_file())

    def test_refuses_branch_with_code_changes(self):
        tamper = self.base / "tamper"
        subprocess.run(["git", "clone", "-q", str(self.remote), str(tamper)], check=True)
        branch = f"audit/{self.run2['run_id']}"
        git(tamper, "checkout", "-q", branch)
        (tamper / "codigo_colado.py").write_text("print('x')\n", encoding="utf-8")
        git(tamper, "add", "-A")
        git(tamper, "commit", "-q", "-m", "colado")
        git(tamper, "push", "-q", "origin", branch)
        rep = cleanup(self.repo, self.run3, self.archive, delete=True)
        self.assertEqual([r["branch"] for r in rep["refused"]], [branch])
        self.assertIn("commits adicionales", rep["refused"][0]["reason"])
        self.assertIn("codigo_colado.py", rep["refused"][0]["reason"])
        self.assertIn(branch, heads(self.remote))
        self.assertNotIn(f"audit/{self.run1['run_id']}", heads(self.remote))

    def test_refuses_when_not_approved(self):
        with self.assertRaises(GitError):
            cleanup(self.repo, self.run2, self.archive, delete=True)
        self.assertEqual(len([h for h in heads(self.remote) if h.startswith("audit/")]), 3)

    def test_observations_need_explicit_opt_in(self):
        run = copy.deepcopy(self.run3)
        low = copy.deepcopy(next(f for f in self.run2["findings"] if f["rule_id"] == "TRN-004"))
        run["findings"] = [low]
        with self.assertRaises(GitError):
            cleanup(self.repo, run, self.archive, delete=False)
        rep = cleanup(self.repo, run, self.archive, delete=False, allow_observations=True)
        self.assertEqual(rep["verdict"], "APROBADO CON OBSERVACIONES")

    def test_default_branch(self):
        self.assertEqual(default_branch(self.repo), "main")

    def test_merge_prompt(self):
        run3 = copy.deepcopy(self.run3)
        run3["target"]["revision"] = self.head
        ids = [self.run1["run_id"], self.run2["run_id"]]
        text = render_merge_prompt(run3, "fix/auditoria", "main", ids)
        for needle in (self.head, "fix/auditoria", "git merge --no-ff origin/fix/auditoria", "CONVERSACIÓN: MISMA",
                       f"git worktree remove --force ../audit-{ids[0].split('-')[0]}", "detente", "sin force"):
            self.assertIn(needle, text)
        self.assertIsNone(render_merge_prompt(run3, "main", "main", ids))


if __name__ == "__main__":
    unittest.main()
