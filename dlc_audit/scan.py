"""Inventario y detectores deterministas. Solo lee el repositorio objetivo."""
from __future__ import annotations

import ast
import fnmatch
import json
import os
import re
from pathlib import Path

from . import __version__
from .common import (
    SCHEMA_VERSION, ROOT, _git, current_ref, finding_id, git_info, load_catalog, load_profile,
    sanitize_url, utc_now,
)

MAX_TEXT_BYTES = 1_000_000
SQL_EXT = {".sql", ".pks", ".pkb", ".pls", ".plb", ".prc", ".fnc", ".trg", ".vw", ".pck"}
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".tar", ".whl", ".exe",
              ".dll", ".so", ".xlsx", ".xls", ".docx", ".pptx", ".ico", ".woff", ".woff2", ".pyc"}
MAX_EVIDENCE = 3


# ---------------------------------------------------------------- contexto

class Ctx:
    def __init__(self, target: Path, files: list[str], sizes: dict[str, int]):
        self.target = target
        self.files = files
        self.sizes = sizes
        self._cache: dict[str, str | None] = {}
        self.limitations: list[str] = []

    def read(self, rel: str) -> str | None:
        if rel not in self._cache:
            path = self.target / rel
            if Path(rel).suffix.lower() in BINARY_EXT or self.sizes.get(rel, 0) > MAX_TEXT_BYTES:
                self._cache[rel] = None
            else:
                try:
                    self._cache[rel] = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    self._cache[rel] = None
        return self._cache[rel]

    def has(self, rel: str) -> bool:
        return rel in self.files

    def root_files(self) -> list[str]:
        return [f for f in self.files if "/" not in f]


def is_skill_file(rel: str) -> bool:
    return Path(rel).name == "SKILL.md"


def is_agent_file(rel: str) -> bool:
    return bool(re.search(r"(^|/)(\.claude/)?agents/[^/]+\.md$", rel))


def domains_of(rel: str) -> set[str]:
    domains: set[str] = set()
    suffix = Path(rel).suffix.lower()
    if (is_skill_file(rel) or is_agent_file(rel) or any(d in f"/{rel}" for d in ("/.claude/", "/.claude-plugin/", "/.agents/"))):
        domains.add("skills-agentes")
    if suffix in SQL_EXT:
        domains.add("sql-plsql")
    if suffix == ".py":
        domains.add("python")
    return domains


def walk(target: Path, exclude_globs: list[str]) -> tuple[list[str], dict[str, int], list[str]]:
    files: list[str] = []
    sizes: dict[str, int] = {}
    excluded: list[str] = []
    for dirpath, dirnames, filenames in os.walk(target):
        rel_dir = Path(dirpath).relative_to(target).as_posix()
        kept = []
        for d in sorted(dirnames):
            rel = d if rel_dir == "." else f"{rel_dir}/{d}"
            if any(fnmatch.fnmatch(rel + "/x", g) or fnmatch.fnmatch(rel, g.rstrip("/*")) for g in exclude_globs):
                excluded.append(rel + "/")
            else:
                kept.append(d)
        dirnames[:] = kept
        for name in sorted(filenames):
            rel = name if rel_dir == "." else f"{rel_dir}/{name}"
            if any(fnmatch.fnmatch(rel, g) for g in exclude_globs):
                excluded.append(rel)
                continue
            full = Path(dirpath) / name
            if full.is_symlink():
                continue
            files.append(rel)
            sizes[rel] = full.stat().st_size
    return files, sizes, excluded


# ---------------------------------------------------------------- helpers de hallazgos

def file_ev(path: str, start: int, end: int, excerpt: str, redacted: bool = False) -> dict:
    ev = {"type": "file", "path": path, "line_start": start, "line_end": end,
          "excerpt": excerpt[:300]}
    if redacted:
        ev["redacted"] = True
    return ev


def absence_ev(path: str, note: str) -> dict:
    return {"type": "absence", "path": path, "note": note}


def make_finding(rule: dict, evidence: list[dict], description: str | None = None,
                 confidence: str = "verified", group: str | None = None) -> dict:
    return {
        "rule_id": rule["id"], "rule_version": rule["version"], "severity": rule["severity"],
        "confidence": confidence, "title": rule["title"],
        "description": description or rule["description"],
        "evidence": evidence, "recommendation": rule["remediation"], "effort": rule["effort"],
        "change_group": group or rule["id"], "detected_by": "scan", "status": "open",
    }


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def span_evidence(path: str, text: str, start: int, end: int) -> dict:
    lines = text.splitlines()
    ls, le = line_of(text, start), line_of(text, max(start, end - 1))
    le = min(le, ls + 4)
    return file_ev(path, ls, le, "\n".join(lines[ls - 1:le]))


def mask_sql(text: str) -> str:
    """Reemplaza comentarios y contenido de cadenas por espacios, conservando saltos de línea."""
    pattern = re.compile(r"--[^\n]*|/\*.*?\*/|'(?:''|[^'])*'", re.S)
    return pattern.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def parse_frontmatter(text: str) -> dict | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    data: dict[str, str] = {}
    key = None
    for line in lines[1:]:
        if line.strip() == "---":
            return data
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            data[key] = "" if val in (">", "|", ">-", "|-") else val.strip("\"'")
        elif key and line.startswith((" ", "\t")):
            data[key] = (data[key] + " " + line.strip()).strip()
    return None


# ---------------------------------------------------------------- detectores transversales

SECRET_PATTERNS = [
    ("clave de acceso AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("token de GitHub", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("clave privada", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("credencial asignada", re.compile(
        r"(?i)\b(?:password|passwd|pwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token)\b"
        r"\s*[:=]\s*['\"]([^'\"\s]{8,})['\"]")),
]
PLACEHOLDER = re.compile(r"(?i)^(x+|\*+|changeme|change_me|your[_-].*|example.*|<.*>|\$\{.*\}|\{\{.*\}\}|none|null|dummy.*|test.*)$")


def _redact_line(line: str, spans: list[tuple[int, int]]) -> str:
    """Sustituye por [REDACTED] cada tramo secreto (se fusionan los solapados)."""
    merged: list[list[int]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    for start, end in reversed(merged):
        line = line[:start] + "[REDACTED]" + line[end:]
    return line


def d_secrets(ctx: Ctx, rule: dict) -> list[dict]:
    out = []
    for rel in ctx.files:
        text = ctx.read(rel)
        if not text:
            continue
        lines = text.splitlines()
        by_line: dict[int, list[tuple[int, int]]] = {}
        labels: set[str] = set()
        total = 0
        for label, pat in SECRET_PATTERNS:
            for m in pat.finditer(text):
                if m.groups() and PLACEHOLDER.match(m.group(1)):
                    continue
                g = 1 if m.groups() else 0
                ln = line_of(text, m.start(g))
                line_start = text.rfind("\n", 0, m.start(g)) + 1
                by_line.setdefault(ln, []).append((m.start(g) - line_start, m.end(g) - line_start))
                labels.add(label)
                total += 1
        if not by_line:
            continue
        # Una evidencia por línea, con TODAS las credenciales de esa línea redactadas.
        evidence = [file_ev(rel, ln, ln, _redact_line(lines[ln - 1], spans).strip(), redacted=True)
                    for ln, spans in sorted(by_line.items())[:MAX_EVIDENCE]]
        out.append(make_finding(rule, evidence,
                                f"Se detectaron {total} posibles credenciales ({', '.join(sorted(labels))}). "
                                "El valor se omite en el informe.", group="secretos"))
    return out


def d_readme(ctx: Ctx, rule: dict) -> list[dict]:
    readmes = [f for f in ctx.root_files() if f.lower().startswith("readme")]
    if not readmes:
        return [make_finding(rule, [absence_ev("README.md", "No existe README en la raíz.")], group="documentacion")]
    text = ctx.read(readmes[0]) or ""
    if len(text.strip()) < 200:
        return [make_finding(rule, [file_ev(readmes[0], 1, max(1, len(text.splitlines())), text.strip()[:300])],
                             "El README tiene menos de 200 caracteres.", confidence="inferential",
                             group="documentacion")]
    return []


def d_changelog(ctx: Ctx, rule: dict) -> list[dict]:
    if any(f.lower().startswith("changelog") for f in ctx.root_files()):
        return []
    return [make_finding(rule, [absence_ev("CHANGELOG.md", "No existe CHANGELOG en la raíz.")], group="documentacion")]


def d_gitignore(ctx: Ctx, rule: dict) -> list[dict]:
    if ctx.has(".gitignore"):
        return []
    return [make_finding(rule, [absence_ev(".gitignore", "No existe .gitignore en la raíz.")], group="higiene")]


def d_tests_ci(ctx: Ctx, rule: dict) -> list[dict]:
    has_tests = any(re.search(r"(^|/)(tests?|spec)/|(^|/)test_[^/]+\.py$|_test\.py$|(^|/)utplsql", f, re.I) for f in ctx.files)
    has_ci = any(f.startswith(".github/workflows/") or f in (".gitlab-ci.yml", "Jenkinsfile", "azure-pipelines.yml")
                 for f in ctx.files)
    if has_tests or has_ci:
        return []
    return [make_finding(rule, [absence_ev("tests/", "No se encontraron pruebas ni pipeline de CI.")],
                         confidence="inferential", group="calidad")]


def d_large_files(ctx: Ctx, rule: dict) -> list[dict]:
    out = []
    for rel in ctx.files:
        if ctx.sizes[rel] > MAX_TEXT_BYTES:
            mb = ctx.sizes[rel] / 1_000_000
            out.append(make_finding(rule, [absence_ev(rel, f"Tamaño {mb:.1f} MB; excede 1 MB.")],
                                    f"El archivo pesa {mb:.1f} MB.", group="higiene"))
            ctx.limitations.append(f"No se analizó el contenido de {rel} (más de 1 MB).")
    return out


# ---------------------------------------------------------------- detectores skills y agentes

def _skill_like(ctx: Ctx):
    for rel in ctx.files:
        if is_skill_file(rel) or is_agent_file(rel):
            text = ctx.read(rel)
            if text is not None:
                yield rel, text, parse_frontmatter(text)


def d_skl_frontmatter(ctx: Ctx, rule: dict) -> list[dict]:
    out = []
    for rel, text, fm in _skill_like(ctx):
        missing = [k for k in ("name", "description") if not (fm or {}).get(k)]
        if fm is None or missing:
            what = "no tiene frontmatter" if fm is None else f"faltan: {', '.join(missing)}"
            first = text.splitlines()[0] if text.strip() else ""
            out.append(make_finding(rule, [file_ev(rel, 1, 1, first)], f"{rel}: {what}.", group="frontmatter"))
    return out


def d_skl_name(ctx: Ctx, rule: dict) -> list[dict]:
    out = []
    for rel, text, fm in _skill_like(ctx):
        name = (fm or {}).get("name")
        if not name:
            continue
        problems = []
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
            problems.append("formato inválido (usa minúsculas, números y guiones; máximo 64)")
        if is_skill_file(rel) and Path(rel).parent.name not in ("", ".") and Path(rel).parent.name != name:
            problems.append(f"no coincide con la carpeta '{Path(rel).parent.name}'")
        if problems:
            ln = next((i for i, l in enumerate(text.splitlines(), 1) if l.startswith("name:")), 1)
            out.append(make_finding(rule, [file_ev(rel, ln, ln, text.splitlines()[ln - 1])],
                                    f"name '{name}': {'; '.join(problems)}.", group="frontmatter"))
    return out


def d_skl_desc_length(ctx: Ctx, rule: dict) -> list[dict]:
    out = []
    for rel, text, fm in _skill_like(ctx):
        desc = (fm or {}).get("description", "")
        if len(desc) > 1024:
            ln = next((i for i, l in enumerate(text.splitlines(), 1) if l.startswith("description:")), 1)
            out.append(make_finding(rule, [file_ev(rel, ln, ln, text.splitlines()[ln - 1])],
                                    f"La descripción tiene {len(desc)} caracteres (límite 1024).", group="frontmatter"))
    return out


def d_skl_agent_tools(ctx: Ctx, rule: dict) -> list[dict]:
    out = []
    for rel, text, fm in _skill_like(ctx):
        if is_agent_file(rel) and fm is not None and "tools" not in fm:
            out.append(make_finding(rule, [file_ev(rel, 1, 1, text.splitlines()[0])],
                                    f"{rel} no declara tools: hereda todas las herramientas.", group="permisos"))
    return out


def d_skl_permissions(ctx: Ctx, rule: dict) -> list[dict]:
    out = []
    for rel in ctx.files:
        if not re.search(r"(^|/)\.claude/settings[^/]*\.json$", rel):
            continue
        text = ctx.read(rel)
        if not text:
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            ctx.limitations.append(f"{rel} no es JSON válido; no se evaluó SKL-008.")
            continue
        perms = data.get("permissions", {}) if isinstance(data, dict) else {}
        bad = [v for v in perms.get("allow", []) if v in ("Bash", "Bash(*)", "Bash(*:*)")]
        if perms.get("defaultMode") == "bypassPermissions":
            bad.append("defaultMode: bypassPermissions")
        if not bad:
            continue
        ev = []
        for token in bad[:MAX_EVIDENCE]:
            needle = token.split(":")[0] if token.startswith("defaultMode") else token
            for i, line in enumerate(text.splitlines(), 1):
                if needle in line:
                    ev.append(file_ev(rel, i, i, line))
                    break
        if ev:
            out.append(make_finding(rule, ev, f"Permisos amplios: {', '.join(bad)}.", group="permisos"))
    return out


def d_skl_length(ctx: Ctx, rule: dict) -> list[dict]:
    out = []
    for rel, text, _ in _skill_like(ctx):
        n = len(text.splitlines())
        if is_skill_file(rel) and n > 500:
            out.append(make_finding(rule, [file_ev(rel, 500, 501, "\n".join(text.splitlines()[499:501]))],
                                    f"{rel} tiene {n} líneas (límite recomendado 500).", group="estructura"))
    return out


def d_skl_links(ctx: Ctx, rule: dict) -> list[dict]:
    out = []
    link = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")
    for rel, text, _ in _skill_like(ctx):
        broken = []
        in_fence = False
        for i, line in enumerate(text.splitlines(), 1):
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for m in link.finditer(line):
                ref = m.group(1)
                if re.match(r"^[a-z][a-z0-9+.-]*:", ref) or ref.startswith(("/", "$")):
                    continue
                dest = os.path.normpath(os.path.join(os.path.dirname(rel), ref)).replace(os.sep, "/")
                if dest not in ctx.files and not any(f.startswith(dest + "/") for f in ctx.files):
                    broken.append((i, line, ref))
        if broken:
            ev = [file_ev(rel, i, i, line) for i, line, _ in broken[:MAX_EVIDENCE]]
            out.append(make_finding(rule, ev, f"{rel}: {len(broken)} enlace(s) rotos ({', '.join(r for *_, r in broken[:MAX_EVIDENCE])}).",
                                    group="referencias"))
    return out


# ---------------------------------------------------------------- detectores SQL/PL-SQL

def _sql_files(ctx: Ctx):
    for rel in ctx.files:
        if Path(rel).suffix.lower() in SQL_EXT:
            text = ctx.read(rel)
            if text is not None:
                yield rel, text, mask_sql(text)


def _per_file(ctx: Ctx, rule: dict, line_pred, desc: str, confidence: str, group: str) -> list[dict]:
    out = []
    for rel, text, masked in _sql_files(ctx):
        raw_lines = text.splitlines()
        hits = [i for i, ml in enumerate(masked.splitlines(), 1) if line_pred(ml)]
        if hits:
            ev = [file_ev(rel, i, i, raw_lines[i - 1]) for i in hits[:MAX_EVIDENCE]]
            out.append(make_finding(rule, ev, f"{rel}: {len(hits)} línea(s). {desc}", confidence=confidence, group=group))
    return out


def d_sql_indent(ctx: Ctx, rule: dict) -> list[dict]:
    return _per_file(ctx, rule, lambda l: bool(re.match(r"^\t* +\S", l)),
                     "Indentación con espacios.", "verified", "formato-sql")


KEYWORDS = ("SELECT FROM WHERE AND OR INSERT INTO UPDATE DELETE CREATE REPLACE PROCEDURE FUNCTION PACKAGE "
            "BEGIN END IS AS EXCEPTION WHEN THEN ELSE ELSIF IF LOOP DECLARE CURSOR RETURN VALUES SET JOIN "
            "LEFT RIGHT INNER OUTER ON GROUP ORDER HAVING UNION COMMIT ROLLBACK").split()
KW_RE = re.compile(r"\b(?:" + "|".join(KEYWORDS) + r")\b")


def d_sql_case(ctx: Ctx, rule: dict) -> list[dict]:
    return _per_file(ctx, rule, lambda l: bool(KW_RE.search(l)),
                     "Palabras reservadas en mayúsculas.", "inferential", "formato-sql")


def d_sql_commas(ctx: Ctx, rule: dict) -> list[dict]:
    return _per_file(ctx, rule, lambda l: bool(re.search(r",\s*$", l)),
                     "Comas al final de línea.", "inferential", "formato-sql")


def _regex_per_file(ctx: Ctx, rule: dict, pattern: re.Pattern, desc: str, confidence: str, group: str) -> list[dict]:
    out = []
    for rel, text, masked in _sql_files(ctx):
        matches = list(pattern.finditer(masked))
        if matches:
            ev = [span_evidence(rel, text, m.start(), m.end()) for m in matches[:MAX_EVIDENCE]]
            out.append(make_finding(rule, ev, f"{rel}: {len(matches)} ocurrencia(s). {desc}",
                                    confidence=confidence, group=group))
    return out


def d_sql_where(ctx: Ctx, rule: dict) -> list[dict]:
    return _regex_per_file(ctx, rule, re.compile(r"\bwhere\s+(?!1\s*=\s*1\b)", re.I),
                           "WHERE sin 1 = 1.", "inferential", "formato-sql")


def d_sql_dynamic(ctx: Ctx, rule: dict) -> list[dict]:
    return _regex_per_file(ctx, rule, re.compile(r"\bexecute\s+immediate\b[^;]*\|\|", re.I),
                           "execute immediate con concatenación.", "inferential", "seguridad-sql")


def d_sql_when_others(ctx: Ctx, rule: dict) -> list[dict]:
    return _regex_per_file(ctx, rule, re.compile(r"\bwhen\s+others\s+then\s+null\s*;", re.I),
                           "Excepción silenciada.", "verified", "excepciones-sql")


def d_sql_select_star(ctx: Ctx, rule: dict) -> list[dict]:
    return _regex_per_file(ctx, rule, re.compile(r"\bselect\s+\*", re.I),
                           "select *.", "inferential", "calidad-sql")


# ---------------------------------------------------------------- detectores Python

def _py_trees(ctx: Ctx):
    for rel in ctx.files:
        if rel.endswith(".py"):
            text = ctx.read(rel)
            if text is None:
                continue
            try:
                yield rel, text, ast.parse(text)
            except SyntaxError:
                ctx.limitations.append(f"{rel} no se pudo analizar (error de sintaxis); sin chequeos PYT.")


def _py_ev(rel: str, text: str, node: ast.AST) -> dict:
    lines = text.splitlines()
    start = node.lineno
    end = min(getattr(node, "end_lineno", start) or start, start + 4)
    return file_ev(rel, start, end, "\n".join(lines[start - 1:end]))


def d_py_requirements(ctx: Ctx, rule: dict) -> list[dict]:
    out = []
    for rel in ctx.files:
        if not re.search(r"(^|/)requirements[^/]*\.txt$", rel):
            continue
        text = ctx.read(rel) or ""
        bad = []
        for i, line in enumerate(text.splitlines(), 1):
            s = line.strip()
            if not s or s.startswith(("#", "-", "git+")) or "==" in s or " @ " in s:
                continue
            bad.append((i, line))
        if bad:
            out.append(make_finding(rule, [file_ev(rel, i, i, l) for i, l in bad[:MAX_EVIDENCE]],
                                    f"{rel}: {len(bad)} dependencia(s) sin versión exacta.", group="dependencias"))
    return out


def d_py_except(ctx: Ctx, rule: dict) -> list[dict]:
    out = []
    for rel, text, tree in _py_trees(ctx):
        hits = [n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler)
                and (n.type is None or all(isinstance(b, ast.Pass) for b in n.body))]
        if hits:
            out.append(make_finding(rule, [_py_ev(rel, text, n) for n in hits[:MAX_EVIDENCE]],
                                    f"{rel}: {len(hits)} manejador(es) genérico(s) o vacío(s).", group="excepciones-py"))
    return out


def d_py_sql_interpolation(ctx: Ctx, rule: dict) -> list[dict]:
    out = []
    for rel, text, tree in _py_trees(ctx):
        hits = []
        for n in ast.walk(tree):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr in ("execute", "executemany", "read_sql", "read_sql_query") and n.args):
                a = n.args[0]
                if (isinstance(a, ast.JoinedStr) or (isinstance(a, ast.BinOp) and isinstance(a.op, (ast.Add, ast.Mod)))
                        or (isinstance(a, ast.Call) and isinstance(a.func, ast.Attribute) and a.func.attr == "format")):
                    hits.append(n)
        if hits:
            out.append(make_finding(rule, [_py_ev(rel, text, n) for n in hits[:MAX_EVIDENCE]],
                                    f"{rel}: {len(hits)} consulta(s) con texto interpolado.",
                                    confidence="inferential", group="seguridad-py"))
    return out


def d_py_s3_hardcode(ctx: Ctx, rule: dict) -> list[dict]:
    out = []
    pat = re.compile(r"""["']s3a?://[A-Za-z0-9._-]+""")
    for rel in ctx.files:
        if not rel.endswith(".py"):
            continue
        text = ctx.read(rel) or ""
        hits = [(i, l) for i, l in enumerate(text.splitlines(), 1)
                if pat.search(l) and not l.lstrip().startswith("#")]
        if hits:
            out.append(make_finding(rule, [file_ev(rel, i, i, l) for i, l in hits[:MAX_EVIDENCE]],
                                    f"{rel}: {len(hits)} ruta(s) S3 fija(s).", confidence="inferential",
                                    group="parametrizacion-py"))
    return out


def d_py_dangerous_calls(ctx: Ctx, rule: dict) -> list[dict]:
    out = []
    for rel, text, tree in _py_trees(ctx):
        hits = []
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            if isinstance(f, ast.Name) and f.id in ("eval", "exec"):
                hits.append(n)
            elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
                if f.value.id == "os" and f.attr == "system":
                    hits.append(n)
                elif f.value.id == "subprocess" and any(
                        k.arg == "shell" and isinstance(k.value, ast.Constant) and k.value.value is True
                        for k in n.keywords):
                    hits.append(n)
        if hits:
            out.append(make_finding(rule, [_py_ev(rel, text, n) for n in hits[:MAX_EVIDENCE]],
                                    f"{rel}: {len(hits)} llamada(s) peligrosa(s).", group="seguridad-py"))
    return out


DETECTORS = {
    "secrets": d_secrets, "readme": d_readme, "changelog": d_changelog, "gitignore": d_gitignore,
    "tests_ci": d_tests_ci, "large_files": d_large_files,
    "skl_frontmatter": d_skl_frontmatter, "skl_name": d_skl_name, "skl_desc_length": d_skl_desc_length,
    "skl_agent_tools": d_skl_agent_tools, "skl_permissions": d_skl_permissions,
    "skl_length": d_skl_length, "skl_links": d_skl_links,
    "sql_indent": d_sql_indent, "sql_case": d_sql_case, "sql_commas": d_sql_commas,
    "sql_where": d_sql_where, "sql_dynamic": d_sql_dynamic, "sql_when_others": d_sql_when_others,
    "sql_select_star": d_sql_select_star,
    "py_requirements": d_py_requirements, "py_except": d_py_except,
    "py_sql_interpolation": d_py_sql_interpolation, "py_s3_hardcode": d_py_s3_hardcode,
    "py_dangerous_calls": d_py_dangerous_calls,
}


# ---------------------------------------------------------------- orquestación

def run_scan(target: Path, profile_name: str = "default", root: Path = ROOT,
             ref: str | None = None, baseline: dict | None = None) -> dict:
    target = target.resolve()
    if not target.is_dir():
        raise SystemExit(f"El objetivo no es un directorio: {target}")
    profile = load_profile(profile_name, root)
    catalog = load_catalog(profile, root)
    started = utc_now()
    files, sizes, excluded = walk(target, profile.get("exclude_globs", []))
    ctx = Ctx(target, files, sizes)

    by_domain: dict[str, int] = {}
    for rel in files:
        for d in domains_of(rel):
            by_domain[d] = by_domain.get(d, 0) + 1
    present = set(by_domain)

    rules_status, findings = [], []
    for rule in catalog.values():
        applies = rule["applies_to"]
        applicable = "*" in applies or bool(present.intersection(applies))
        entry = {"id": rule["id"], "version": rule["version"], "method": rule["method"]}
        if not applicable:
            entry.update(status="not_applicable", note=f"Sin archivos de dominio: {', '.join(applies)}.")
        elif rule["method"] == "judgment":
            entry["status"] = "pending"
        else:
            entry["status"] = "evaluated"
            findings.extend(DETECTORS[rule["detector"]](ctx, rule))
        rules_status.append(entry)

    for f in findings:
        f["id"] = finding_id(f["rule_id"], f["evidence"])

    info = git_info(target)
    limitations = sorted(set(ctx.limitations))
    if info["dirty"]:
        limitations.append("El repositorio objetivo tiene cambios sin commitear; la auditoría no es reproducible por revisión.")
    if info["revision"] == "no-git":
        limitations.append("El objetivo no es un repositorio git (o git no está disponible); no hay revisión registrada.")
    limitations.append("Los hallazgos con confidence=inferential provienen de detección heurística y pueden ser falsos positivos.")

    name = target.name
    stamp = started.replace("-", "").replace(":", "")[:15] + "Z"
    round_no = (baseline.get("round", 1) + 1) if baseline else 1
    run_id = f"{stamp}-{name}" if round_no == 1 else f"{stamp}-r{round_no}-{name}"
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "auditor": {"name": "dlc.audit", "version": __version__,
                    "revision": _git(root, "rev-parse", "HEAD") or "no-git"},
        "profile": {"name": profile["name"], "version": profile["version"]},
        "round": round_no,
        "baseline_run_id": baseline["run_id"] if baseline else None,
        "target": {"name": name, "path": str(target), **info,
                   "url": sanitize_url(_git(target, "remote", "get-url", "origin") or ""),
                   "ref": ref or current_ref(target)},
        "started_at": started, "finished_at": None,
        "coverage": {"files_total": len(files), "files_by_domain": dict(sorted(by_domain.items())),
                     "excluded": excluded},
        "rules": rules_status,
        "executive_summary": "",
        "limitations": limitations,
        "findings": findings,
    }
