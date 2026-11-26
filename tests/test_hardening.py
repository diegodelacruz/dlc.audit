"""Endurecimiento: datos no confiables (cierre del integrador, refs, remotos) y fuga de secretos."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from dlc_audit.closure import check_closure
from dlc_audit.common import save_json
from dlc_audit.gitops import GitError, cycle_branches, fetch, publish, resolve_ref
from dlc_audit.render import render_integrator_prompt, render_prompts, render_report
from dlc_audit.scan import run_scan
from test_audit import build_target
from test_protocol import finish, git


def make_remote(base: Path, name: str = "origin.git") -> tuple[Path, Path]:
    src = build_target(base / f"src-{name}")
    git(src, "branch", "-M", "main")
    remote = base / name
    subprocess.run(["git", "clone", "-q", "--bare", str(src), str(remote)], check=True)
    git(src, "remote", "add", "origin", str(remote))
    return src, remote


class HardeningTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_all_secrets_on_a_line_are_redacted(self):
        a, b = "AKIA" + "AAAAAAAAAAAAAAAA", "AKIA" + "BBBBBBBBBBBBBBBB"
        pwd = "hunter2" + "hunter2"
        repo = self.base / "t"
        repo.mkdir()
        (repo / "conf.py").write_text(f"X = '{a}'; Y = '{b}'; password = '{pwd}'\n", encoding="utf-8")
        run = run_scan(repo)
        blob = json.dumps(run)
        for secret in (a, b, pwd):
            self.assertNotIn(secret, blob)
        sec = [f for f in run["findings"] if f["rule_id"] == "TRN-001"]
        self.assertEqual(len(sec), 1)
        # Una sola evidencia por línea: no se repite la misma línea redactada.
        self.assertEqual(len({(e["path"], e["line_start"]) for e in sec[0]["evidence"]}), len(sec[0]["evidence"]))

    def test_publish_only_ships_known_deliverables(self):
        src, remote = make_remote(self.base)
        info = fetch(str(remote), self.base / "work", "main")
        run = finish(run_scan(Path(info["path"]), ref="main"), Path(info["path"]))
        out = self.base / "run"
        save_json(out / "hallazgos.json", run)
        index = render_prompts(run, out)
        render_integrator_prompt(run, out)
        render_report(run, out, index, has_integrator_prompt=True)
        (out / "notas-privadas.txt").write_text("no debe salir\n", encoding="utf-8")
        (out / "prompts" / "borrador.tmp").write_text("tampoco\n", encoding="utf-8")
        res = publish(out / "hallazgos.json", push=False)
        joined = " ".join(res["files"])
        self.assertNotIn("notas-privadas", joined)
        self.assertNotIn("borrador.tmp", joined)
        self.assertIn("prompt-integrador.md", joined)
        self.assertIn("prompts/INDEX.md", joined)

    def test_fetch_refuses_same_name_different_repo(self):
        _, remote_a = make_remote(self.base / "a")
        _, remote_b = make_remote(self.base / "b")
        self.assertEqual(remote_a.name, remote_b.name)
        work = self.base / "work"
        fetch(str(remote_a), work, "main")
        with self.assertRaises(GitError):
            fetch(str(remote_b), work, "main")
        fetch(str(remote_a), work, "main")  # el mismo repositorio sí se reutiliza

    def test_refs_cannot_inject_git_options(self):
        _, remote = make_remote(self.base)
        info = fetch(str(remote), self.base / "work", "main")
        for bad in ("--help", "-x", "main;touch pwned", "--output=" + str(self.base / "pwned")):
            with self.assertRaises(GitError, msg=bad):
                resolve_ref(Path(info["path"]), bad)
        self.assertFalse((self.base / "pwned").exists())

    def test_closure_rejects_option_like_revisions(self):
        _, remote = make_remote(self.base)
        info = fetch(str(remote), self.base / "work", "main")
        repo = Path(info["path"])
        run = run_scan(repo, ref="main")
        fid = run["findings"][0]["id"]
        marker = self.base / "pwned"
        cierre = {"run_id": run["run_id"], "base_revision": run["target"]["revision"],
                  "head_revision": "--output=" + str(marker), "branch": "main",
                  "findings": [{"id": fid, "status": "fixed", "commits": ["--output=" + str(marker)],
                                "files": ["x"], "verification": "v"}]}
        check = check_closure(run, cierre, repo)
        self.assertTrue(any("head_revision" in e and "inválid" in e for e in check["errors"]))
        cierre["head_revision"] = run["target"]["revision"]
        check = check_closure(run, cierre, repo)
        self.assertTrue(any("commit" in e and "inválid" in e for e in check["errors"]))
        self.assertFalse(marker.exists())

    def test_cycle_ignores_malformed_run_ids_from_remote_data(self):
        src, remote = make_remote(self.base)
        info = fetch(str(remote), self.base / "work", "main")
        repo = Path(info["path"])
        final = {"run_id": "20261126T060000Z-origin", "baseline_run_id": "../../etc:passwd"}
        entries, notes = cycle_branches(repo, final)
        self.assertEqual(entries, [])
        self.assertTrue(any("inválid" in n for n in notes))


if __name__ == "__main__":
    unittest.main()
