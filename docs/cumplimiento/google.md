# Cumplimiento: Google (Antigravity)

Fecha de consulta: **2026-11-26**.

## Fuentes consultadas

| Fuente | URL | Resultado | Lectura |
|---|---|---|---|
| Antigravity: agent skills | https://antigravity.google/docs/skills.md | Accesible (HTTP 200) | Texto completo (7.509 caracteres), citas literales |

La página no muestra fecha ni versión. En octubre esta fuente era inaccesible; las fuentes secundarias de entonces ya no se usan.

## Requisitos

| ID | Requisito | Cita literal | Estado |
|---|---|---|---|
| G-01 | `description` obligatoria; `name` opcional | "`description` \| Yes \| A clear description of what the skill does and when to use it." y "`name` \| No \| A unique identifier for the skill (lowercase, hyphens for spaces). Defaults to the folder name if not provided." | Verificado |
| G-02 | Descubrimiento | App: "`<workspace-root>/.agents/skills/<skill-folder>/`" y "`~/.gemini/config/skills/<skill-folder>/`". "Antigravity also reads `.agents/skills/` in each parent folder up to the repository root." CLI: añade "`~/.gemini/config/plugins/<plugin-folder>/skills/`", y carga "`~/.gemini/antigravity-cli/skills/`" y "`~/.gemini/skills/`", que la App no lee. IDE: ruta heredada "`~/.gemini/antigravity/skills/`". "Antigravity defaults to `.agents/skills`, but still maintains backward compatibility for `.agent/skills`." | Verificado. La sección del IDE no menciona carpetas padre |
| G-03 | Estándar abierto | "Skills are an [open standard](https://agentskills.io/home) for extending agent capabilities." | Verificado |
| G-04 | Scripts | "`scripts/       # Optional executable scripts`"; "Optional helper scripts and data schemas the agent can execute." | Verificado. Terminal, permisos, red y git no se documentan: **[No verificado]** |
| G-05 | Límites y versión | No hay límite de longitud de `name` ni de `description`, ni fecha ni versión. Solo: `name` en "lowercase, hyphens for spaces" | Verificado la **ausencia** |

## Aplicación a este repositorio

- `.agents/skills/` es una copia generada de `skills/` y cubre App, CLI e IDE (G-02).
- Como `name` es opcional aquí (G-01) pero obligatorio en la especificación abierta y en Claude y Codex, nuestras fuentes siempre lo incluyen.
- La ejecución de nuestro flujo (shell, git con push) en Antigravity **no está documentada**: soporte L1, ejecución **[No verificado]**.

## Pendiente

- Verificar en una instalación real cómo Antigravity trata campos desconocidos y si dispone de terminal con acceso a red.
- La lectura de octubre sobre Gemini CLI (`GEMINI.md`) no se relee: es otro producto.
