"""Skills portables: fuente única, copias generadas y validación de portabilidad."""
from __future__ import annotations

import contextlib
import io
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

from dlc_audit.__main__ import main
from dlc_audit.common import ROOT, PolicyError
from dlc_audit.scan import domains_of, run_scan
from dlc_audit.skills import TARGETS, check_portability, check_sync, list_skills, package_zip, sync

GOOD = """---
name: demo-skill
description: Hace una tarea de demostración. Úsala cuando el usuario pida una demostración.
---

# Demo

Sigue [la referencia](references/ref.md).
"""


def make_root(base: Path, skill_md: str = GOOD, name: str = "demo-skill") -> Path:
    root = base / "repo"
    skill = root / "skills" / name
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text(skill_md, encoding="utf-8")
    (skill / "references" / "ref.md").write_text("# Referencia\n", encoding="utf-8")
    return root


class RepositorySkillsTests(unittest.TestCase):
    """Estas pruebas fallan si alguien edita una copia a mano o rompe la portabilidad."""

    def test_repository_skills_are_portable(self):
        self.assertEqual(check_portability(ROOT), [])

    def test_repository_copies_are_in_sync(self):
        self.assertEqual(check_sync(ROOT), [], "Ejecute: python -m dlc_audit skills sync")

    def test_expected_skills_exist_in_every_target(self):
        names = {s.name for s in list_skills(ROOT)}
        self.assertEqual(names, {"audit-repo", "reaudit"})
        for target in TARGETS:
            for n in names:
                self.assertTrue((ROOT / target / n / "SKILL.md").is_file(), f"{target}/{n}")

    def test_subagent_points_to_the_shared_reference(self):
        agent = (ROOT / ".claude/agents/dlc-auditor.md").read_text(encoding="utf-8")
        self.assertIn(".claude/skills/audit-repo/references/evaluacion-juicio.md", agent)
        self.assertTrue((ROOT / ".claude/skills/audit-repo/references/evaluacion-juicio.md").is_file())

    def test_agents_directory_belongs_to_the_skills_domain(self):
        self.assertIn("skills-agentes", domains_of(".agents/skills/x/references/a.md"))
        self.assertIn("skills-agentes", domains_of(".agents/skills/x/SKILL.md"))

    def test_cli_check_passes_on_the_repository(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(main(["skills", "check"]), 0)
        self.assertIn("sincronizadas", buf.getvalue())


class PortabilityRulesTests(unittest.TestCase):
    def check(self, skill_md: str, name: str = "demo-skill") -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            return check_portability(make_root(Path(tmp), skill_md, name))

    def test_valid_skill_passes(self):
        self.assertEqual(self.check(GOOD), [])

    def test_rejects_proprietary_frontmatter_field(self):
        bad = GOOD.replace("---\n\n#", "argument-hint: <x>\n---\n\n#", 1)
        self.assertTrue(any("campos no portables" in e and "argument-hint" in e for e in self.check(bad)))

    def test_rejects_forbidden_tokens_in_body(self):
        for token in ("$ARGUMENTS", "AskUserQuestion", ".claude/"):
            errors = self.check(GOOD + f"\nUsa {token} aquí.\n")
            self.assertTrue(any(token in e for e in errors), token)

    def test_rejects_invalid_names(self):
        self.assertTrue(any("no puede contener" in e for e in
                            self.check(GOOD.replace("demo-skill", "mi-claude-skill"), "mi-claude-skill")))
        self.assertTrue(any("no puede contener" in e for e in
                            self.check(GOOD.replace("demo-skill", "anthropic-tool"), "anthropic-tool")))
        self.assertTrue(any("inválido" in e for e in
                            self.check(GOOD.replace("demo-skill", "Demo_Skill"), "Demo_Skill")))
        self.assertTrue(any("no coincide con la carpeta" in e for e in
                            self.check(GOOD.replace("name: demo-skill", "name: otro-nombre"))))

    def test_rejects_bad_description(self):
        self.assertTrue(any("etiquetas tipo XML" in e for e in
                            self.check(GOOD.replace("tarea de demostración", "tarea <run_id> de demostración"))))
        long_desc = "x" * 1025
        errors = self.check(GOOD.replace("Hace una tarea de demostración. Úsala cuando el usuario pida una demostración.", long_desc))
        self.assertTrue(any("1025 caracteres" in e for e in errors))
        self.assertTrue(any("falta description" in e for e in self.check("---\nname: demo-skill\n---\ncuerpo\n")))

    def test_rejects_missing_frontmatter_broken_links_and_long_files(self):
        self.assertTrue(any("sin frontmatter" in e for e in self.check("sin frontmatter\n")))
        self.assertTrue(any("enlace roto" in e for e in self.check(GOOD + "\nVer [x](references/no-existe.md).\n")))
        self.assertTrue(any("más de 500 líneas" in e for e in self.check(GOOD + "linea\n" * 600)))


class SyncTests(unittest.TestCase):
    def test_sync_generates_identical_copies_and_repairs_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(Path(tmp))
            self.assertTrue(check_sync(root))                    # sin generar: faltan las copias
            sync(root)
            self.assertEqual(check_sync(root), [])
            for target in TARGETS:
                for rel in ("SKILL.md", "references/ref.md"):
                    self.assertEqual((root / target / "demo-skill" / rel).read_bytes(),
                                     (root / "skills" / "demo-skill" / rel).read_bytes())

            (root / ".claude/skills/demo-skill/SKILL.md").write_text("editado a mano\n", encoding="utf-8")
            (root / ".agents/skills/demo-skill/extra.md").write_text("sobra\n", encoding="utf-8")
            (root / ".agents/skills/demo-skill/references/ref.md").unlink()
            (root / ".claude/skills/huerfana").mkdir()
            (root / ".claude/skills/huerfana/SKILL.md").write_text("x\n", encoding="utf-8")
            joined = "\n".join(check_sync(root))
            for expected in ("distinto .claude/skills/demo-skill/SKILL.md", "sobrante .agents/skills/demo-skill/extra.md",
                             "falta .agents/skills/demo-skill/references/ref.md", "sobrante .claude/skills/huerfana/"):
                self.assertIn(expected, joined)

            sync(root)
            self.assertEqual(check_sync(root), [])
            self.assertFalse((root / ".claude/skills/huerfana").exists())

    def test_sync_refuses_a_non_portable_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(Path(tmp), GOOD + "\nUsa $ARGUMENTS.\n")
            with self.assertRaises(ValueError):
                sync(root)
            self.assertFalse((root / ".claude").exists())


class PackageTests(unittest.TestCase):
    def test_package_is_written_outside_the_repository_and_is_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(Path(tmp))
            first = package_zip(root, Path(tmp) / "out")
            data = first.read_bytes()
            with zipfile.ZipFile(first) as zf:
                self.assertEqual(sorted(zf.namelist()), ["demo-skill/SKILL.md", "demo-skill/references/ref.md"])
            self.assertEqual(package_zip(root, Path(tmp) / "out").read_bytes(), data)

    def test_package_refuses_to_write_inside_the_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PolicyError):
                package_zip(make_root(Path(tmp)), ROOT / "paquetes")
        self.assertFalse((ROOT / "paquetes").exists())

    def test_package_defaults_to_the_work_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["DLC_AUDIT_WORKDIR"] = str(Path(tmp) / "wd")
            self.addCleanup(os.environ.pop, "DLC_AUDIT_WORKDIR", None)
            path = package_zip(make_root(Path(tmp)))
            self.assertEqual(path.parent, (Path(tmp) / "wd" / "packages").resolve())


class SelfAuditTests(unittest.TestCase):
    def test_scan_of_this_repository_finds_no_deterministic_issue_in_skills(self):
        run = run_scan(ROOT, ref="main")
        skill_rules = {f["rule_id"] for f in run["findings"] if f["rule_id"].startswith("SKL")}
        self.assertEqual(skill_rules, set(), f"El propio repositorio incumple reglas de skills: {skill_rules}")


if __name__ == "__main__":
    unittest.main()
