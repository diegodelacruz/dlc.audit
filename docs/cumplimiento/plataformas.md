# Cómo se cargan las skills en cada plataforma

Fecha de consulta: **2026-10-19**. Detalle de fuentes y estados en `openai.md`, `anthropic.md` y `google.md`.

## Resumen

| Plataforma | Mecanismo equivalente a skills | Verificación | Adaptador en este repositorio |
|---|---|---|---|
| Claude (Claude Code) | Carpeta con `SKILL.md` en `~/.claude/skills/` o `.claude/skills/` | Verificado (Anthropic) | `plataformas/claude/skills/auditor/SKILL.md` |
| ChatGPT | Skills en ChatGPT: no se obtuvo documentación oficial accesible. El equivalente más cercano verificado es el estándar Agent Skills (carpeta con `SKILL.md`) y la estructura de plugin de Codex | [No verificado] para ChatGPT | `plataformas/chatgpt/skills/auditor/SKILL.md` |
| Antigravity | Skills en `.agents/skills/<nombre>/SKILL.md` según fuentes secundarias | [No verificado] | `plataformas/antigravity/.agents/skills/auditor/SKILL.md` |

## Claude

- Se instala copiando la carpeta `plataformas/claude/skills/auditor/` a `~/.claude/skills/` (personal) o a `.claude/skills/` del proyecto.
- Claude carga `name` y `description` al inicio y lee `SKILL.md` cuando la tarea coincide (A-04 en `anthropic.md`).

## ChatGPT

- No se pudo verificar cómo ChatGPT carga skills personalizadas. Por eso el adaptador deja el contenido en `plataformas/chatgpt/skills/auditor/SKILL.md`, con la misma estructura que el estándar abierto, y no incluye manifiesto de plugin.
- Alternativa documentada: el plugin de Codex, con `.codex-plugin/plugin.json` y la carpeta `skills/` (O-02 en `openai.md`). Se descarta por ahora porque es un formato de Codex, no de ChatGPT.
- Ver `docs/decisiones/20261019-adaptador-chatgpt-sin-manifiesto.md`.

## Antigravity

- Se usa el directorio `.agents/skills/` según fuentes secundarias (G-02 en `google.md`, [No verificado]).
- Las reglas (`.agents/rules`) y los flujos no se adaptan en v1: el auditor no los requiere y su requisito no está verificado.

## Pendiente

- Verificar los requisitos de ChatGPT y de Antigravity cuando las documentaciones oficiales sean accesibles desde el entorno de auditoría. Al hacerlo, actualizar esta página y registrar la decisión nueva en `docs/decisiones/`.
