# Cumplimiento: OpenAI (Codex y ChatGPT)

Fecha de consulta: **2026-11-26**.

## Fuentes consultadas

| Fuente | URL | Resultado | Lectura |
|---|---|---|---|
| Codex: skills | https://learn.chatgpt.com/docs/build-skills.md (destino de la redirección permanente 308 desde https://developers.openai.com/codex/skills) | Accesible (HTTP 200) | Texto completo (unos 11.400 caracteres), citas literales |
| Skills en ChatGPT (Centro de ayuda) | https://help.openai.com/en/articles/20001066-skills-in-chatgpt | Accesible (HTTP 200) | Texto completo, citas literales |

Ninguna de las dos páginas muestra fecha. La de ChatGPT dice "Updated: last month".

## Requisitos: Codex

| ID | Requisito | Cita literal | Estado |
|---|---|---|---|
| O-01 | `name` y `description` obligatorios | "The `SKILL.md` file must include `name` and `description`." | Verificado |
| O-02 | Descubrimiento | "Codex scans `.agents/skills` in every directory from your current working directory up to the repository root." Rutas: `$CWD/.agents/skills`, `$CWD/../.agents/skills`, `$REPO_ROOT/.agents/skills`, usuario `$HOME/.agents/skills`, administrador `/etc/codex/skills` y las del sistema ("Bundled with Codex by OpenAI.") | Verificado |
| O-03 | Estándar abierto | "Skills build on the open agent skills standard" | Verificado |
| O-04 | Límites de `name` y `description` | No hay límite de caracteres. Solo el presupuesto de la lista inicial: "this list uses at most 2% of the model's context window, or 8,000 characters when the context window is unknown." y la guía "write concise descriptions with clear scope and boundaries." | Verificado la **ausencia** de límite en esa página |
| O-05 | Scripts | "A skill is a directory with a `SKILL.md` file plus optional scripts and references."; "Prefer instructions over scripts unless you need deterministic behavior or external tooling." Sandbox, permisos, red y git: no aparecen | Verificado; lo no documentado queda **[No verificado]** |
| O-06 | Skills y plugins | "Skills are the authoring format for reusable workflows."; "Plugins distribute reusable skills and connectors through the universal plugin directory shared by ChatGPT and Codex."; "Direct skill folders are best for local authoring and repo-scoped workflows."; "Standalone skills are available in the ChatGPT desktop app, Codex CLI, and IDE extension." | Verificado. **No** dice literalmente que el plugin sea innecesario: recomienda las carpetas directas para este caso |

## Requisitos: ChatGPT

| ID | Requisito | Cita literal | Estado |
|---|---|---|---|
| O-07 | Disponibilidad | "Skills are available to eligible ChatGPT Business, Enterprise, Healthcare, and Edu users" y depende de "workspace settings and product availability". No aparecen los planes Free ni Plus | Verificado; planes personales **[No verificado]** |
| O-08 | Subida | "Upload a skill: Go to **Skills**, select **Create**, then select **Upload from your computer**." No se documenta formato ni tamaño de archivo | Verificado; formato **[No verificado]** |
| O-09 | Escaneo | "When you upload a skill, ChatGPT scans it before it becomes available."; "Some skills may be marked **Needs Review**..."; "Skills that appear to contain content or behavior that could pose a risk may be marked **Blocked** and cannot be used." | Verificado |
| O-10 | Contenido de una skill | "A skill can include instructions, examples, and code."; "It can also include reusable steps and scripts for more structured work." | Verificado |
| O-11 | Ejecución, red, GitHub y git | No aparecen en la página. Solo: "External services or resources used by a skill may have separate storage and processing terms." | **[No verificado]** |
| O-12 | Otros productos | "Skills can also be supported in Codex and other OpenAI products." La página no afirma que ChatGPT siga el estándar abierto | Verificado; adhesión de ChatGPT al estándar **[No verificado]** |

## Aplicación a este repositorio

- Codex: `.agents/skills/` es una copia generada de `skills/` (O-02). Las fuentes solo usan `name` y `description` (O-01), sin campos propietarios.
- ChatGPT: `python -m dlc_audit skills package` genera el `.zip`. **Que ChatGPT ejecute Python o haga `git push` no está documentado (O-11)**, así que su soporte es L1 (instalable) y la ejecución consta como **[No verificado]**.
- Riesgo **[Inferencial]**: un flujo que borra ramas y hace push puede disparar el estado *Blocked* (O-09). La página no dice qué lo activa.

## Pendiente

- El manifiesto de plugin de Codex (`.codex-plugin/plugin.json`) y `agents/openai.yaml` solo se vieron en octubre en un ejemplo de `openai/plugins`; hoy no se releyeron. Importan solo si se decide distribuir fuera del repositorio.
- No se verificó si Codex lee `AGENTS.md` ni cómo trata campos desconocidos del frontmatter.
