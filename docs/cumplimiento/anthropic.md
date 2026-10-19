# Cumplimiento: Anthropic

Fecha de consulta: **2026-10-19**. Versión: la página no declara número de versión; se registra el contenido consultado en esta fecha.

## Fuentes consultadas

| Fuente | URL | Resultado |
|---|---|---|
| Agent Skills: visión general | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview | Accesible (HTTP 200) |
| Agent Skills: buenas prácticas | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices | Accesible (HTTP 200) |

## Requisitos verificados

| ID | Requisito | Fuente | Estado |
|---|---|---|---|
| A-01 | `SKILL.md` con frontmatter YAML que incluye `name` y `description` | visión general | Verificado |
| A-02 | `name`: máximo 64 caracteres, solo minúsculas, números y guiones; sin etiquetas XML; no puede contener "anthropic" ni "claude" | visión general y buenas prácticas | Verificado |
| A-03 | `description`: no vacía, máximo 1024 caracteres, sin etiquetas XML; debe describir qué hace y cuándo usarla | visión general | Verificado |
| A-04 | Solo `name` y `description` se cargan al inicio; el cuerpo de `SKILL.md` se lee cuando la tarea coincide | visión general (niveles de carga) | Verificado |
| A-05 | Recursos adicionales (scripts, referencias) se leen solo cuando se necesitan | visión general | Verificado |
| A-06 | Ubicación en Claude Code: `~/.claude/skills/` (personal) o `.claude/skills/` (proyecto) | visión general | Verificado |
| A-07 | Buenas prácticas: mantener `SKILL.md` conciso; cada token compite con el historial de la conversación | buenas prácticas | Verificado |
| A-08 | En la API, las dependencias de paquetes deben listarse en `SKILL.md`; la API no tiene acceso a red en tiempo de ejecución | buenas prácticas | Verificado |
| A-09 | claude.ai no ofrece administración centralizada ni distribución organizativa de skills personalizadas | visión general | Verificado |

## Aplicación a este repositorio

- `skills/auditor/SKILL.md` cumple A-01 a A-03 (name `auditor`; description de 1024 caracteres o menos; sin palabras reservadas). El validador comprueba los límites.
- La instalación en Claude Code usa `plataformas/claude/skills/auditor/` (ver `plataformas.md`).

## Limitaciones

- No se verificó el comportamiento de la carga en cada superficie (claude.ai, API, Claude Code) más allá de lo que describe la página.
- [No verificado] que las URL futuras de la documentación se mantengan.
