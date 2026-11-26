"""Repositorio de demostración: ficticio, con defectos conocidos y sin secretos.

Sirve para probar el ciclo completo (auditar, corregir, re-auditar, cerrar) sobre un repositorio propio
descartable. Se genera en el directorio temporal, nunca dentro de dlc.audit.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from .common import ensure_outside_repo, workdir

NAME = "demo-auditoria"
IDENTITY = ["-c", "user.name=dlc.audit", "-c", "user.email=dlc-audit@users.noreply.github.com"]

SQL = (
    "CREATE OR REPLACE PROCEDURE p_demo IS\n"
    "begin\n"
    "  select a,\n"
    "         b\n"
    "    from t\n"
    "   where x = 1;\n"
    "  select * from t where y = 2;\n"
    "  execute immediate 'delete from ' || v_tabla;\n"
    "exception\n"
    "\twhen others then null;\n"
    "end;\n"
    "/\n"
)

PYTHON = (
    "import subprocess\n"
    "\n"
    "\n"
    "def procesar(cur, nombre):\n"
    "    cur.execute(f\"select * from t where n = '{nombre}'\")\n"
    "    try:\n"
    "        pass\n"
    "    except:\n"
    "        pass\n"
    "    subprocess.run('ls', shell=True)\n"
    "    ruta = '" + "s3" + "://bucket-demo/datos'\n"
    "    return ruta\n"
)

FILES = {
    ".claude/skills/Demo_Skill/SKILL.md": "---\nname: Demo_Skill\n---\nConsulta [la guia](refs/guia.md) antes de empezar.\n",
    ".claude/agents/revisor.md": "---\nname: revisor\ndescription: Agente de demostración.\n---\nRevisa el código.\n",
    ".claude/settings.json": '{\n  "permissions": {\n    "allow": [\n      "Bash(*)"\n    ]\n  }\n}\n',
    "sql/proceso_demo.sql": SQL,
    "src/app.py": PYTHON,
    "requirements.txt": "fastapi\nuvicorn==0.30.0\n",
}

# Reglas que el auditor debe detectar en este repositorio (como mínimo).
EXPECTED = [
    "TRN-002", "TRN-003", "TRN-004", "TRN-006",
    "SKL-001", "SKL-002", "SKL-006", "SKL-008", "SKL-010",
    "SQL-001", "SQL-002", "SQL-003", "SQL-004", "SQL-006", "SQL-007", "SQL-011",
    "PYT-001", "PYT-002", "PYT-004", "PYT-005", "PYT-007",
]


def build_demo(dest: Path | None = None) -> dict:
    """Crea el repositorio de demostración (git, rama main, un commit) y devuelve su ruta y commit."""
    dest = ensure_outside_repo(dest if dest else workdir() / "demo" / NAME)
    if dest.exists() and any(dest.iterdir()):
        raise FileExistsError(f"{dest} ya existe y no está vacío.")
    for rel, text in FILES.items():
        path = dest / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", str(dest), *IDENTITY, *args], capture_output=True, text=True, check=True).stdout.strip()
    git("init", "-q")
    git("checkout", "-q", "-b", "main")
    git("add", "-A")
    git("commit", "-q", "-m", "Repositorio de demostración con defectos conocidos")
    return {"path": str(dest), "revision": git("rev-parse", "HEAD"), "expected": list(EXPECTED)}
