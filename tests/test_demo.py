"""El repositorio de demostración: defectos conocidos, sin secretos y corregible por completo."""
from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

from dlc_audit.__main__ import main
from dlc_audit.common import ROOT, PolicyError, load_profile, verdict
from dlc_audit.demo import EXPECTED, FILES, build_demo
from dlc_audit.scan import run_scan
from dlc_audit.validate import validate_run
from test_protocol import finish

FIXES = {
    "README.md": "# Demo\n\nRepositorio de demostración para probar el ciclo de auditoría. Contiene una skill, un agente, "
                 "un procedimiento SQL y un módulo Python.\n\n## Requisitos\n\nPython 3.11 o superior.\n\n## Uso\n\n"
                 "Se instalan las dependencias con pip y se prueba con unittest.\n\n## Estructura\n\n"
                 "Las carpetas son sql, src, tests y .claude.\n",
    "CHANGELOG.md": "# Changelog\n\n## [Unreleased]\n",
    ".gitignore": "__pycache__/\n",
    "tests/test_app.py": "import unittest\n\n\nclass T(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n",
    ".claude/skills/demo-skill/SKILL.md": ("---\nname: demo-skill\ndescription: Hace una tarea de demostración. "
                                           "Úsala cuando el usuario pida una demostración.\n---\n\n# Demo\n"),
    ".claude/agents/revisor.md": "---\nname: revisor\ndescription: Agente de demostración.\ntools: Read\n---\nRevisa el código.\n",
    ".claude/settings.json": '{\n  "permissions": {\n    "allow": [\n      "Bash(npm run test *)"\n    ]\n  }\n}\n',
    "sql/proceso_demo.sql": ("create or replace procedure p_demo is\nbegin\n\tselect a\n\t, b\n\tfrom t\n\twhere 1 = 1\n"
                             "\tand x = 1;\n\texecute immediate 'delete from t where v = :1' using v_valor;\nexception\n"
                             "\twhen others then\n\t\traise;\nend;\n/\n"),
    "src/app.py": ("import logging\nimport subprocess\n\n\ndef procesar(cur, nombre, ruta):\n"
                   "    cur.execute(\"select n from t where n = :nombre\", {\"nombre\": nombre})\n    try:\n"
                   "        subprocess.run([\"ls\"], check=True)\n    except subprocess.CalledProcessError:\n"
                   "        logging.exception(\"fallo\")\n        raise\n    return ruta\n"),
    "requirements.txt": "fastapi==0.115.0\nuvicorn==0.30.0\n",
}


def rule_ids(run: dict) -> set[str]:
    return {f["rule_id"] for f in run["findings"]}


class DemoRepositoryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_scan_detects_exactly_the_expected_rules(self):
        info = build_demo(self.base / "demo")
        run = run_scan(Path(info["path"]), ref="main")
        self.assertEqual(rule_ids(run), set(EXPECTED))

    def test_demo_has_no_secrets_so_github_will_not_block_the_push(self):
        info = build_demo(self.base / "demo")
        self.assertNotIn("TRN-001", rule_ids(run_scan(Path(info["path"]), ref="main")))

    def test_demo_is_a_single_commit_on_main_with_a_generic_identity(self):
        import subprocess
        info = build_demo(self.base / "demo")
        repo = info["path"]
        out = subprocess.run(["git", "-C", repo, "log", "--format=%an|%ae", "--all"], capture_output=True, text=True).stdout.split()
        self.assertEqual(out, ["dlc.audit|dlc-audit@users.noreply.github.com"])
        self.assertEqual(subprocess.run(["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"],
                                        capture_output=True, text=True).stdout.strip(), "main")

    def test_demo_is_fully_fixable_and_then_approved(self):
        info = build_demo(self.base / "demo")
        repo = Path(info["path"])
        shutil.rmtree(repo / ".claude" / "skills" / "Demo_Skill")
        for rel, text in FIXES.items():
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
        run = run_scan(repo, ref="main")
        self.assertEqual(run["findings"], [], f"El demo corregido aún tiene hallazgos: {rule_ids(run)}")
        run = finish(run, repo)
        errors, _ = validate_run(run, repo, final=True)
        self.assertEqual(errors, [])
        self.assertEqual(verdict(run["findings"], load_profile("default")), "APROBADO")

    def test_the_fixed_readme_is_long_enough_for_the_rule(self):
        self.assertGreaterEqual(len(FIXES["README.md"].strip()), 200)

    def test_every_defective_file_is_covered_by_a_fix(self):
        covered = set(FIXES) | {".claude/skills/Demo_Skill/SKILL.md"}
        self.assertTrue(set(FILES) <= covered | set(FIXES))

    def test_refuses_the_repository_directory_and_non_empty_destinations(self):
        with self.assertRaises(PolicyError):
            build_demo(ROOT / "demo")
        self.assertFalse((ROOT / "demo").exists())
        build_demo(self.base / "demo")
        with self.assertRaises(FileExistsError):
            build_demo(self.base / "demo")

    def test_purge_removes_the_demo_directory_too(self):
        import os
        os.environ["DLC_AUDIT_WORKDIR"] = str(self.base / "wd")
        self.addCleanup(os.environ.pop, "DLC_AUDIT_WORKDIR", None)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["demo"]), 0)
            self.assertTrue((self.base / "wd" / "demo" / "demo-auditoria").is_dir())
            self.assertEqual(main(["purge", "demo-auditoria"]), 0)
        self.assertFalse((self.base / "wd" / "demo" / "demo-auditoria").exists())

    def test_cli_prints_the_expected_rules(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(main(["demo", "--out", str(self.base / "cli")]), 0)
        text = buf.getvalue()
        for rid in EXPECTED:
            self.assertIn(rid, text)


if __name__ == "__main__":
    unittest.main()
