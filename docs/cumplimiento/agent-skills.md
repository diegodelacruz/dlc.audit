# Cumplimiento: estándar abierto Agent Skills

Fecha de consulta: **2026-11-26**.

## Fuentes consultadas

| Fuente | URL | Resultado | Lectura |
|---|---|---|---|
| Especificación Agent Skills | https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx | Accesible (HTTP 200) | Texto completo (7.136 caracteres), citas literales |

La página no muestra versión ni fecha. Su frontmatter solo contiene `title` y `description`.

## Requisitos

| ID | Requisito | Cita literal | Estado |
|---|---|---|---|
| S-01 | `name` y `description` son obligatorios | `name`: "Max 64 characters. Lowercase letters, numbers, and hyphens only. Must not start or end with a hyphen." `description`: "Max 1024 characters. Non-empty. Describes what the skill does and when to use it." | Verificado |
| S-02 | Restricciones de `name` | "Must be 1-64 characters"; "Must not start or end with a hyphen (`-`)"; "Must not contain consecutive hyphens (`--`)"; "Must match the parent directory name" | Verificado |
| S-03 | Restricciones de `description` | "Must be 1-1024 characters"; "Should describe both what the skill does and when to use it" | Verificado. La tabla dice "Max 1024" y la sección "1-1024" |
| S-04 | Campos opcionales | `license`, `compatibility` ("Max 500 characters"), `metadata` ("Arbitrary key-value mapping") y `allowed-tools` ("(Experimental)"). La tabla del frontmatter no lista otros campos (observación del lector, no cita) | Verificado |
| S-05 | Estructura de directorios | "A skill is a directory containing, at minimum, a `SKILL.md` file"; `scripts/`, `references/` y `assets/` son convenciones: "The conventions below are recommendations" | Verificado |
| S-06 | Tamaño y profundidad | "Keep your main `SKILL.md` under 500 lines."; "Instructions (< 5000 tokens recommended)"; "Keep file references one level deep from `SKILL.md`." | Verificado |

## Aplicación a este repositorio

- `python -m dlc_audit skills check` valida S-01 a S-03 y S-06 (`name` igual a su carpeta, longitud, guiones, `description` de hasta 1.024 caracteres, `SKILL.md` de hasta 500 líneas, referencias a un nivel).
- Las fuentes en `skills/` usan **solo** `name` y `description`, aunque S-04 permite cuatro campos opcionales más. Es una decisión deliberada de portabilidad; ver `anthropic.md` (A-07) y `openai.md`.
- Las referencias de las skills viven en `references/` (S-05).

## Pendiente

- La especificación no publica versión: si cambia, no hay forma de detectarlo salvo releerla. Releer en cada cambio de skills.
