# Cumplimiento: Anthropic (Claude Code, Skills API y claude.ai)

Fecha de consulta: **2026-11-26**.

## Fuentes consultadas

| Fuente | URL | Resultado | Lectura |
|---|---|---|---|
| Agent Skills: visión general | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview | Accesible (HTTP 200) | Texto completo (unos 23.600 caracteres), citas literales |
| Claude Code: skills | https://code.claude.com/docs/en/skills | Accesible | Texto literal de los primeros 79.898 de 121.124 caracteres; el resto llegó como resumen y **no se usó** |

| Claude Code: subagentes | https://code.claude.com/docs/en/sub-agents | Accesible | Literal de los primeros 79.890 de 114.792 caracteres; el resto llegó como resumen y no se usó |
| Claude Code: permisos | https://code.claude.com/docs/en/permissions | Accesible | Literal de los primeros 79.888 de 94.755 caracteres; el resto llegó como resumen y no se usó |
| Claude Code: hooks | https://code.claude.com/docs/en/hooks | Accesible | Literal en los tramos 0 a 79.900 y 179.900 a 301.722 (de unos 301.700); el tramo central llegó como resumen y no se usó |
| Claude Code: ajustes | https://code.claude.com/docs/en/settings | Accesible | Texto completo, citas literales. La página `settings-reference.md` llegó en parte como resumen y no se usó |

Ninguna de las páginas muestra fecha de publicación. La de Claude Code cita versiones de la herramienta (hasta v2.1.331).

## Requisitos

| ID | Requisito | Cita literal | Estado |
|---|---|---|---|
| A-01 | `name` y `description` son obligatorios en la API | "**Required fields:** `name` and `description`" (visión general) | Verificado |
| A-02 | Restricciones de `name` | "Maximum 64 characters"; "Must contain only lowercase letters, numbers, and hyphens"; "Cannot contain reserved words: `anthropic`, `claude`"; "Cannot contain XML tags". La página no aclara si la comprobación es por subcadena o por palabra completa | Verificado |
| A-03 | Restricciones de `description` | "Must be non-empty"; "Maximum 1,024 characters"; "Cannot contain XML tags"; "The `description` must include both what the Skill does and when Claude should use it." | Verificado |
| A-04 | Niveles de carga | Nivel 1 "Metadata (always loaded)" (~100 tokens por skill); nivel 2 "Instructions (loaded when triggered)" (menos de 5k tokens); nivel 3 "Resources and code (loaded as needed)" | Verificado |
| A-05 | Ubicación en Claude Code | "place them in `~/.claude/skills/` (personal) or `.claude/skills/` (project)". La página de Claude Code añade skills anidadas (`<subdir>/.claude/skills/`), de plugin y del directorio `--add-dir` | Verificado |
| A-06 | Campos del frontmatter en Claude Code | "All fields are optional. Only `description` is recommended so Claude knows when to use the skill." La tabla lista 20 campos, entre ellos `argument-hint`, `allowed-tools`, `model`, `context`, `agent`, `hooks`, `paths`, `shell`, `metadata`, `license` y `compatibility` | Verificado |
| A-07 | Campos desconocidos | En Claude Code: "Claude Code ignores a field it doesn't recognize without reporting an error." Fuera de Claude Code: "If you include any field the spec doesn't allow, packaging or upload fails with a hard error instead of ignoring the field". Campos admitidos allí: `allowed-tools`, `compatibility`, `description`, `license`, `metadata` y `name` | Verificado |
| A-08 | Longitud del cuerpo | "Keep `SKILL.md` under 500 lines." (Claude Code; la especificación abierta lo repite en S-06) | Verificado |
| A-09 | Red | Claude Code: "Skills have the same network access as any other program on the user’s computer." API: "Skills cannot make external API calls or access the internet." claude.ai: "Depending on user/admin settings, Skills might have full, partial, or no network access." | Verificado |
| A-10 | Nombres rechazados por Claude Code | "Claude Code refuses a command name or a frontmatter `name` that contains characters such as these": espacio de ancho cero, carácter de control, espacio distinto del simple entre palabras y "`<` or `>`". Nombres reservados: `synced` y `anthropic-skills` | Verificado |
| A-11 | Truncado del listado | "the combined `description` and `when_to_use` text is truncated at 1,536 characters in the skill listing" | Verificado |
| A-12 | Estándar abierto | "Claude Code skills follow the [Agent Skills](https://agentskills.io) open standard, which works across multiple AI tools." | Verificado |
| A-13 | claude.ai | "Upload your own Skills as zip files." | Verificado |

## Requisitos: subagentes, permisos, ajustes y hooks de Claude Code

| ID | Requisito | Cita literal | Estado |
|---|---|---|---|
| A-14 | Un subagente sin `tools` hereda todas las herramientas | "Inherits every tool available to subagents if omitted."; "Subagents inherit the built-in tools and MCP tools available in the main conversation, narrowed by two filters." | Verificado |
| A-15 | Campos de un subagente | "Only `name` and `description` are required."; "Claude Code ignores a field it doesn't recognize without reporting an error."; sin `description`: "Claude Code skips the file and writes the reason to the debug log." | Verificado |
| A-16 | Ubicación de los subagentes | "`.claude/agents/` \| Current project"; "`~/.claude/agents/` \| All your projects"; "Plugin's `agents/` directory"; además ajustes administrados y `--agents` | Verificado |
| A-17 | Reglas de permiso de Bash | "Permission rules follow the format `Tool` or `Tool(specifier)`."; "`Bash(*)` is equivalent to `Bash` and matches all Bash commands."; "Allow rules let Claude Code use the specified tool without manual approval." | Verificado |
| A-18 | Modo `bypassPermissions` | "Skips permission prompts, except for the actions no mode auto-approves"; "Claude Code skips permission prompts, including for writes to protected paths such as `.git` and `.claude`."; "Only use this mode in isolated environments like containers or VMs where Claude Code can't cause damage." | Verificado |
| A-19 | Desactivar ese modo | "To prevent `bypassPermissions` or `auto` mode from being used, set `permissions.disableBypassPermissionsMode` or `permissions.disableAutoMode` to `"disable"`."; "These are most useful in managed settings where they can't be overridden." | Verificado |
| A-20 | `defaultMode` y su efecto en ajustes de proyecto | "Set the default permission mode for new sessions"; "`auto` and `bypassPermissions` don't take effect from project or local settings" | Verificado. La lista completa de valores de `defaultMode` **no** se leyó literalmente |
| A-21 | Qué ajustes se versionan | `.claude/settings.json`: "commit it so teammates get it"; `.claude/settings.local.json`: "Claude Code keeps it out of git when it creates the file"; hooks de proyecto: "Yes, can be committed to the repo" | Verificado |
| A-22 | Advertencia de seguridad de los hooks | "Command hooks execute shell commands with your full user permissions."; "They can modify, delete, or access any files your user account can access."; "Review and test all hook commands before adding them to your configuration." | Verificado |
| A-23 | Buenas prácticas de seguridad de los hooks | "Validate and sanitize inputs"; "Always quote shell variables"; "Block path traversal"; "Use absolute paths"; "Skip sensitive files" | Verificado |
| A-24 | Hooks de un repositorio no confiable | "Claude Code never shows the dialog and treats the folder as trusted, so hooks committed in a repository's `.claude/settings.json` run in a folder you've never trusted" (en sesiones `-p` o del SDK) | Verificado |

## Aplicación a este repositorio

- Las reglas `SKL-006`, `SKL-007`, `SKL-008` y `SKL-016` se apoyan en A-14 a A-24. `SKL-008` solo marca permisos `Bash` sin restricción; el modo `bypassPermissions` en ajustes de proyecto no tiene efecto (A-20), por eso es un hallazgo menor aparte (`SKL-016`).
- `skills check` valida A-01 a A-03, A-08 y A-10 en `name` y `description`: sin "claude" ni "anthropic", sin `<` ni `>`, de hasta 64 y 1.024 caracteres.
- **Por qué solo `name` y `description` en `skills/`:** (1) A-07, la subida a claude.ai o a la API falla con error si hay un campo fuera de su lista; `argument-hint`, por ejemplo, es un campo válido de Claude Code (A-06) pero rompería esa subida. (2) Codex y Antigravity no documentan qué hacen con campos desconocidos (`openai.md` y `google.md`).
- A-11 (1.536 caracteres en el listado de Claude Code) es menos estricto que el límite de 1.024 de A-03, que es el que se aplica.

## Pendiente

- Releer el resto de la página de Claude Code (el 34% final llegó como resumen): permisos, solución de problemas y compartición.
- A-02 no aclara si "claude" se rechaza como subcadena o como palabra. `skills check` rechaza la subcadena (criterio conservador).
- La página de buenas prácticas y la afirmación de octubre sobre administración centralizada en claude.ai no se releyeron hoy.
- **[No verificado]:** la lista completa de valores de `permissions.defaultMode`, el ajuste `skipDangerousModePermissionPrompt` y un ejemplo literal de la clave `ask`; solo aparecen en resúmenes de modelo. La sintaxis heredada `Bash(x:*)` tampoco se verificó, por lo que `SKL-008` no la evalúa.
