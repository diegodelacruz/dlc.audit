"""Integridad del repositorio: estructura, enlaces y referencias sin cabos sueltos."""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

from dlc_audit.common import ROOT

LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")
CODE = re.compile(r"`((?:docs|rules|profiles|templates|skills|tests|dlc_audit|\.claude|\.agents)/[A-Za-z0-9_./\-]+)`")
SEPARATOR = re.compile(r"^\|[\s:|-]+\|$")
# Rutas que describen archivos de OTRO repositorio (el auditado), no de este.
OTHER_REPO_PATHS = {".claude/settings.json", ".claude/settings.local.json"}


def tracked() -> list[str]:
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True)
    if out.returncode != 0:
        raise unittest.SkipTest("git no disponible")
    return [f for f in out.stdout.split() if (ROOT / f).exists()]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def outside_code_fences(text: str):
    inside = False
    for n, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith(("```", "~~~")):
            inside = not inside
            continue
        if not inside:
            yield n, line


def is_historical(rel: str, text: str) -> bool:
    """Decisiones heredadas de octubre: citan rutas del diseño anterior y lo declaran."""
    return rel.startswith("docs/decisiones/") and "Origen: rama `claude/gallant-babbage-2srymf`" in text


class LinksAndPathsTests(unittest.TestCase):
    def test_relative_markdown_links_resolve(self):
        broken = []
        for rel in (f for f in tracked() if f.endswith(".md")):
            for n, line in outside_code_fences(read(rel)):
                for ref in LINK.findall(line):
                    if re.match(r"^[a-z][a-z0-9+.-]*:", ref) or ref.startswith("$"):
                        continue
                    if not ((ROOT / rel).parent / ref).exists():
                        broken.append(f"{rel}:{n} -> {ref}")
        self.assertEqual(broken, [])

    def test_repository_paths_cited_in_backticks_exist(self):
        missing = []
        for rel in (f for f in tracked() if f.endswith(".md")):
            text = read(rel)
            if is_historical(rel, text):
                continue
            for n, line in outside_code_fences(text):
                for ref in CODE.findall(line):
                    if any(c in ref for c in "*<>{}") or "AAAAMMDD" in ref or ref in OTHER_REPO_PATHS:
                        continue
                    if not (ROOT / ref).exists():
                        missing.append(f"{rel}:{n} -> {ref}")
        self.assertEqual(missing, [])

    def test_every_document_under_docs_is_referenced_by_another_file(self):
        files = tracked()
        texts = {f: read(f) for f in files if f.endswith((".md", ".py", ".json", ".tmpl"))}
        orphans = []
        for rel in (f for f in files if f.startswith("docs/") and f.endswith(".md") and not f.endswith("README.md")):
            name = Path(rel).name
            if not any(q != rel and (name in t or rel in t) for q, t in texts.items()):
                orphans.append(rel)
        self.assertEqual(orphans, [])


class DocumentedCommandsTests(unittest.TestCase):
    def test_documented_commands_exist_and_every_command_is_documented(self):
        helptxt = subprocess.run([sys.executable, "-m", "dlc_audit", "--help"], capture_output=True, text=True, cwd=ROOT).stdout
        cmds = set(re.search(r"\{([a-z,\-]+)\}", helptxt).group(1).split(","))
        docs = "\n".join(read(f) for f in tracked()
                         if f.endswith(".md") and not f.startswith("docs/decisiones/") and f != "CHANGELOG.md")
        used = set(re.findall(r"python -m dlc_audit ([a-z][a-z\-]*)", docs))
        self.assertEqual(used - cmds, set(), "se documentan comandos que no existen")
        self.assertEqual(cmds - used, set(), "hay comandos sin documentar")


class StructureTests(unittest.TestCase):
    def test_readme_structure_matches_the_tree(self):
        block = read("README.md").split("## Estructura")[1].split("```")[1]
        listed = [line.split()[0] for line in block.splitlines() if line.strip()]
        for entry in listed:
            self.assertTrue((ROOT / entry.rstrip("/")).exists(), f"README lista '{entry}' y no existe")
        top = {f.split("/")[0] for f in tracked()}
        uncovered = [t for t in sorted(top) if t != "README.md"
                     and not any(e.rstrip("/").split("/")[0] == t for e in listed)]
        self.assertEqual(uncovered, [], "elementos de primer nivel sin documentar en README")

    def test_no_junk_files_or_empty_directories(self):
        junk = [f for f in tracked() if re.search(r"__pycache__|\.pyc$|\.DS_Store|Thumbs\.db|\.swp$|~$", f)]
        self.assertEqual(junk, [])
        empty = [str(d.relative_to(ROOT)) for d in ROOT.rglob("*")
                 if d.is_dir() and ".git" not in d.parts and "__pycache__" not in d.parts and not any(d.iterdir())]
        self.assertEqual(empty, [])


class MarkdownTablesTests(unittest.TestCase):
    def test_every_table_has_a_header_separator(self):
        broken = []
        for rel in (f for f in tracked() if f.endswith(".md")):
            lines, inside, i = read(rel).split("\n"), False, 0
            while i < len(lines):
                if lines[i].strip().startswith(("```", "~~~")):
                    inside = not inside
                if not inside and lines[i].startswith("|") and (i == 0 or not lines[i - 1].startswith("|")):
                    j = i
                    while j < len(lines) and lines[j].startswith("|"):
                        j += 1
                    if j - i < 2 or not SEPARATOR.match(lines[i + 1].strip()):
                        broken.append(f"{rel}:{i + 1}")
                    i = j
                    continue
                i += 1
        self.assertEqual(broken, [], "tablas sin cabecera: probablemente una línea en blanco las parte")


class PythonHygieneTests(unittest.TestCase):
    def test_no_unused_imports(self):
        unused = []
        for rel in (f for f in tracked() if f.endswith(".py") and not f.endswith("__init__.py")):
            src = read(rel)
            tree = ast.parse(src)
            imported = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        imported[(a.asname or a.name).split(".")[0]] = node.lineno
                elif isinstance(node, ast.ImportFrom):
                    for a in node.names:
                        imported[a.asname or a.name] = node.lineno
            used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
            for name, line in imported.items():
                if name != "annotations" and name not in used and f'"{name}"' not in src:
                    unused.append(f"{rel}:{line} {name}")
        self.assertEqual(unused, [])

    def test_module_docstrings_do_not_use_retired_terms(self):
        for rel in (f for f in tracked() if f.endswith(".py")):
            doc = (ast.get_docstring(ast.parse(read(rel))) or "").lower()
            self.assertNotIn("archivado", doc, rel)


class VersionAndIdsTests(unittest.TestCase):
    def test_version_matches_the_changelog(self):
        ver = re.search(r'__version__ = "([^"]+)"', read("dlc_audit/__init__.py")).group(1)
        heads = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", read("CHANGELOG.md"), re.M)
        self.assertEqual(heads[0], ver)
        self.assertEqual(heads, sorted(heads, key=lambda v: tuple(map(int, v.split("."))), reverse=True))
        self.assertEqual(len(heads), len(set(heads)))

    def test_rule_ids_cited_in_current_documents_exist(self):
        rules = {r["id"] for f in (ROOT / "rules").glob("*.json") for r in json.loads(f.read_text(encoding="utf-8"))["rules"]}
        for rel in (f for f in tracked() if f.endswith((".md", ".py", ".tmpl")) and f != "CHANGELOG.md"
                    and not f.startswith("docs/decisiones/")):
            for rid in set(re.findall(r"\b(?:TRN|SKL|SQL|PYT)-\d{3}\b", read(rel))):
                self.assertIn(rid, rules, f"{rel} cita {rid}")


if __name__ == "__main__":
    unittest.main()
