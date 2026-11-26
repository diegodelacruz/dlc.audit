# Cómo carga cada plataforma las skills

Fecha de consulta: **2026-11-26**. Detalle de fuentes, citas literales y estados en `agent-skills.md`, `anthropic.md`, `openai.md` y `google.md`. Decisiones de diseño en `../multiplataforma.md`.

## Resumen

| Plataforma | Dónde carga las skills | Copia en este repositorio | Verificación |
|---|---|---|---|
| Claude Code | `.claude/skills/<nombre>/SKILL.md` (personal, proyecto, anidada, plugin) | `.claude/skills/` | Verificado (A-05) |
| Codex | `.agents/skills/` desde el directorio actual hasta la raíz del repositorio | `.agents/skills/` | Verificado (O-02) |
| Antigravity | `.agents/skills/<skill>/SKILL.md` en App, CLI e IDE, y carpetas padre | `.agents/skills/` | Verificado (G-02) |
| ChatGPT | Subida desde *Skills, Create, Upload from your computer* | `python -m dlc_audit skills package` | Subida verificada (O-08); ejecución **[No verificado]** (O-11) |

## Qué comparten

Las cuatro cargan una carpeta con `SKILL.md`. Claude Code (A-12), Codex (O-03) y Antigravity (G-03) declaran seguir el estándar abierto Agent Skills (`agent-skills.md`). ChatGPT no lo afirma (O-12). El nombre de la carpeta y el `name` deben coincidir (S-02).

## Qué difiere

| Aspecto | Claude Code | Codex | Antigravity | ChatGPT |
|---|---|---|---|---|
| Campos obligatorios | Ninguno (`description` recomendada) | `name` y `description` | `description` | No documentado |
| Campos desconocidos | Se ignoran | No documentado | No documentado | No documentado |
| Límites de `name` y `description` | 64 y 1.024 (API); listado truncado a 1.536 | No hay | No hay | No documentado |
| Scripts | Sí | Sí ("Prefer instructions over scripts") | Sí | Incluidos; ejecución no documentada |
| Red | Misma que el equipo del usuario | No documentada | No documentada | No documentada |

## Correcciones a lo afirmado antes

La relectura literal del 2026-11-26 corrige dos afirmaciones de la definición del bloque 1 (`../multiplataforma.md`):

1. **Plugin de Codex.** Se dijo que el plugin "no es necesario". La página no lo dice literalmente: recomienda "Direct skill folders" para "local authoring and repo-scoped workflows" y presenta el plugin como mecanismo de distribución (O-06). La conclusión práctica no cambia: dentro de un clon basta `.agents/skills/`.
2. **Campos propietarios.** Se justificó quitar `argument-hint` por falta de documentación en Codex y Antigravity. Hay una razón más fuerte: la subida a claude.ai o a la API falla con error ante cualquier campo fuera de su lista (A-07).

## Pendiente

- Verificar la ejecución real del flujo en Codex, Antigravity y ChatGPT cuando alguien pueda probarlas (hoy solo Claude Code es probable de punta a punta).
