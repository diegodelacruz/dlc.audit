"""Documentación verificable: cumplimiento con fuentes, registro de decisiones y criterios."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from dlc_audit.common import ROOT

DOCS = ROOT / "docs"
ESTADOS = ("Verificado", "[No verificado]")
# El nombre del repositorio real que se auditó antes no debe aparecer en ningún archivo versionado.
REAL_NAME = "apex" + "[.-]skills"


def table_rows(text: str) -> list[list[str]]:
    rows = []
    for line in text.splitlines():
        if line.startswith("|") and not re.match(r"^\|[\s:-]+\|", line):
            rows.append([c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))])
    return rows


class ComplianceDocsTests(unittest.TestCase):
    files = ("agent-skills", "anthropic", "openai", "google", "plataformas")

    def test_every_file_declares_a_consultation_date(self):
        for name in self.files:
            text = (DOCS / "cumplimiento" / f"{name}.md").read_text(encoding="utf-8")
            self.assertRegex(text, r"Fecha de consulta: \*\*\d{4}-\d{2}-\d{2}\*\*", name)

    def test_requirements_have_unique_ids_and_a_state(self):
        for name in ("agent-skills", "anthropic", "openai", "google"):
            text = (DOCS / "cumplimiento" / f"{name}.md").read_text(encoding="utf-8")
            ids = []
            for row in table_rows(text):
                if re.fullmatch(r"[A-Z]-\d{2}", row[0]):
                    ids.append(row[0])
                    self.assertGreaterEqual(len(row), 4, f"{name} {row[0]}")
                    self.assertTrue(any(e in row[-1] for e in ESTADOS), f"{name} {row[0]}: estado ausente")
                    self.assertIn('"', row[-2] if len(row) > 4 else row[2], f"{name} {row[0]}: sin cita literal")
            self.assertTrue(ids, name)
            self.assertEqual(len(ids), len(set(ids)), f"{name}: IDs repetidos")

    def test_sources_are_https_urls_with_a_reading_note(self):
        for name in ("agent-skills", "anthropic", "openai", "google"):
            text = (DOCS / "cumplimiento" / f"{name}.md").read_text(encoding="utf-8")
            section = text.split("## Fuentes consultadas")[1].split("##")[0]
            rows = [r for r in table_rows(section) if r and r[0] != "Fuente"]
            self.assertTrue(rows, name)
            for row in rows:
                self.assertRegex(row[1], r"https://", f"{name}: {row[0]}")
                self.assertGreaterEqual(len(row), 4, f"{name}: falta la columna Lectura")

    def test_cross_references_to_requirement_ids_resolve(self):
        known = set()
        for name in ("agent-skills", "anthropic", "openai", "google"):
            known |= {r[0] for r in table_rows((DOCS / "cumplimiento" / f"{name}.md").read_text(encoding="utf-8"))
                      if re.fullmatch(r"[A-Z]-\d{2}", r[0])}
        for path in (DOCS / "multiplataforma.md", DOCS / "cumplimiento" / "plataformas.md", DOCS / "criterios.md"):
            for ref in re.findall(r"\b([SAOG]-\d{2})\b", path.read_text(encoding="utf-8")):
                self.assertIn(ref, known, f"{path.name} cita {ref}, que no existe")


class DecisionsTests(unittest.TestCase):
    def files(self):
        return sorted(p for p in (DOCS / "decisiones").glob("2*.md"))

    def test_naming_title_and_state(self):
        self.assertGreaterEqual(len(self.files()), 12)
        for p in self.files():
            self.assertRegex(p.name, r"^\d{8}-[a-z0-9-]+\.md$")
            text = p.read_text(encoding="utf-8")
            self.assertRegex(text.splitlines()[0], r"^# \d{4}-\d{2}-\d{2} ", p.name)
            self.assertRegex(text, r"(?m)^Estado: \S", p.name)

    def test_index_lists_every_decision(self):
        index = (DOCS / "decisiones" / "README.md").read_text(encoding="utf-8")
        for p in self.files():
            self.assertIn(f"({p.name})", index, f"{p.name} no está en el índice")

    def test_replaced_decisions_say_by_which_one(self):
        for p in self.files():
            text = p.read_text(encoding="utf-8")
            if re.search(r"(?m)^Estado: Reemplazada", text):
                self.assertRegex(text, r"## Vigencia en dlc\.audit", p.name)
                self.assertRegex(text, r"`[^`]+\.md`|`docs/[^`]+`|`profiles/[^`]+`|`python -m dlc_audit[^`]*`", p.name)


class CriteriaTests(unittest.TestCase):
    def test_all_twelve_criteria_are_traced(self):
        text = (DOCS / "criterios.md").read_text(encoding="utf-8")
        rows = {r[0] for r in table_rows(text)}
        for n in range(1, 13):
            self.assertIn(f"C{n}", rows)
        for row in table_rows(text):
            if re.fullmatch(r"C\d+", row[0]):
                self.assertTrue(any(s in row[2] for s in ("Vigente", "Adaptado", "Reemplazado", "Parcial", "No implementado")), row[0])


class NoRealRepositoryNamesTests(unittest.TestCase):
    def test_no_tracked_text_file_names_a_real_audited_repository(self):
        import subprocess
        out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True)
        if out.returncode != 0:
            raise unittest.SkipTest("git no disponible")
        for rel in out.stdout.split():
            path = ROOT / rel
            if path.suffix in (".md", ".json", ".py", ".tmpl", ".txt") and path.is_file():
                self.assertIsNone(re.search(REAL_NAME, path.read_text(encoding="utf-8"), re.I), rel)


if __name__ == "__main__":
    unittest.main()
