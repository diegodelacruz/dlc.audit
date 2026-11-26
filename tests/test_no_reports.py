"""Política: este repositorio NO guarda informes de auditoría, ni en git ni en disco."""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from dlc_audit.__main__ import main
from dlc_audit.common import ROOT, PolicyError, ensure_outside_repo, save_json, workdir
from dlc_audit.gitops import fetch
from dlc_audit.render import render_prompts
from dlc_audit.scan import run_scan
from test_audit import build_target
from test_protocol import finish

FORBIDDEN_DIRS = ("audits/", "auditorias/", ".audit/", "work/", "runs/", "clones/")
REPORT_NAMES = re.compile(
    r"(^|/)(hallazgos[^/]*\.json|informe[^/]*\.md|prompt-integrador[^/]*\.md|prompt-merge[^/]*\.md|"
    r"cierre[^/]*\.json|closure-check[^/]*\.json|ciclo-[^/]*\.json|baseline[^/]*\.json)$")


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True)
    if out.returncode != 0:
        raise unittest.SkipTest("git no disponible o no es un clon")
    return out.stdout.split()


def snapshot() -> set[str]:
    skip = {".git", "__pycache__"}
    found = set()
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for f in filenames:
            found.add(str((Path(dirpath) / f).relative_to(ROOT)))
    return found


class NoReportsPolicyTests(unittest.TestCase):
    def test_repository_tracks_no_reports(self):
        bad = [f for f in tracked_files()
               if f.startswith(FORBIDDEN_DIRS) or REPORT_NAMES.search(f)]
        self.assertEqual(bad, [], f"Archivos con aspecto de informe versionados: {bad}")

    def test_no_tracked_json_is_an_audit_run(self):
        for f in tracked_files():
            if f.endswith(".json"):
                data = json.loads((ROOT / f).read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self.assertFalse({"run_id", "findings"} <= data.keys(), f"{f} parece un run de auditoría")

    def test_guard_rejects_paths_inside_the_repository(self):
        for inside in (ROOT / "audits" / "x", ROOT / "informe.md", ROOT / "docs" / "run"):
            with self.assertRaises(PolicyError):
                ensure_outside_repo(inside)
        with self.assertRaises(PolicyError):
            save_json(ROOT / "audits" / "r" / "hallazgos.json", {"a": 1})
        self.assertFalse((ROOT / "audits" / "r").exists())

    def test_workdir_is_outside_the_repository_and_env_cannot_move_it_inside(self):
        self.assertNotIn(ROOT, workdir().parents)
        old = os.environ.get("DLC_AUDIT_WORKDIR")
        os.environ["DLC_AUDIT_WORKDIR"] = str(ROOT / "work")
        try:
            with self.assertRaises(PolicyError):
                workdir()
        finally:
            os.environ.pop("DLC_AUDIT_WORKDIR") if old is None else os.environ.update(DLC_AUDIT_WORKDIR=old)

    def test_render_and_fetch_refuse_to_write_inside_the_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = build_target(Path(tmp))
            run = finish(run_scan(target), target)
            with self.assertRaises(PolicyError):
                render_prompts(run, ROOT / "audits" / "x")
            with self.assertRaises(PolicyError):
                fetch(str(target), ROOT / "work")
        self.assertFalse((ROOT / "audits" / "x").exists())

    def test_full_cli_cycle_leaves_repository_untouched_and_purge_removes_workdir(self):
        before = snapshot()
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["DLC_AUDIT_WORKDIR"] = str(Path(tmp) / "wd")
            self.addCleanup(os.environ.pop, "DLC_AUDIT_WORKDIR", None)
            target = build_target(Path(tmp))
            subprocess.run(["git", "-C", str(target), "branch", "-M", "main"], check=True)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(main(["fetch", str(target), "--ref", "main"]), 0)
                clone = re.search(r"Ruta: (.+)", buf.getvalue()).group(1).strip()
                self.assertEqual(main(["scan", clone, "--ref", "main"]), 0)
            out = buf.getvalue()
            run_path = Path(re.search(r"Archivo: (.+)", out).group(1).strip())
            self.assertTrue(run_path.is_file())
            self.assertIn(str(Path(tmp) / "wd"), str(run_path))
            self.assertEqual(snapshot(), before)           # nada nuevo dentro de dlc.audit
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["purge", "clones"]), 0)   # nombre reservado: no borra la carpeta de clones
            self.assertTrue(run_path.is_file())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["purge", run_path.parent.parent.name]), 0)
            self.assertFalse(run_path.exists())
            self.assertEqual(snapshot(), before)

    def test_cli_reports_policy_errors_without_traceback(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["fetch", "no-existe-ni-es-url", "--dest", str(ROOT / "work")])
        self.assertNotEqual(rc, 0)
        self.assertIn("ERROR", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
