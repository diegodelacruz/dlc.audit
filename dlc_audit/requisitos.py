"""Requisitos oficiales: docs/cumplimiento/ es la fuente única; aquí solo se leen."""
from __future__ import annotations

import re
from pathlib import Path

from .common import ROOT

ID_RE = re.compile(r"^[A-Z]-\d{2}$")


def load_requirements(root: Path = ROOT) -> dict[str, dict]:
    """{id: {title, doc, verified}} de las tablas de requisitos de docs/cumplimiento/."""
    found: dict[str, dict] = {}
    folder = root / "docs" / "cumplimiento"
    if not folder.is_dir():
        return found
    for path in sorted(folder.glob("*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
            if len(cells) >= 4 and ID_RE.match(cells[0]):
                found[cells[0]] = {"title": cells[1], "doc": f"docs/cumplimiento/{path.name}",
                                   "verified": cells[-1].startswith("Verificado")}
    return found
