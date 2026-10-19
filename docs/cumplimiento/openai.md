# Cumplimiento: OpenAI

Fecha de consulta: **2026-10-19**.

## Fuentes consultadas

| Fuente | URL | Resultado |
|---|---|---|
| Codex: skills (documentación oficial) | https://developers.openai.com/codex/skills | **No accesible** desde el entorno de auditoría (proxy 403 / sin resolución DNS) |
| Repositorio `openai/skills` | https://raw.githubusercontent.com/openai/skills/main/README.md | Accesible. Declara el repositorio **obsoleto** y remite a `openai/plugins` y a `https://developers.openai.com/codex/plugins/build` (no accesible) |
| Repositorio `openai/plugins` | https://raw.githubusercontent.com/openai/plugins/main/README.md | Accesible. Describe la estructura de plugins de Codex |
| Especificación Agent Skills (estándar abierto) | https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx | Accesible. Estándar que Codex declara seguir (según la página de skills de Codex citada en la fuente de `openai/skills`) |
| Repositorio `openai/codex` `AGENTS.md` | https://raw.githubusercontent.com/openai/codex/main/AGENTS.md | Devuelve 404. [No verificado] |

## Requisitos

| ID | Requisito | Fuente | Estado |
|---|---|---|---|
| O-01 | Una skill es una carpeta con `SKILL.md`; `name` y `description` son obligatorios | Especificación Agent Skills (https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx) | Verificado en la especificación abierta. [No verificado] que Codex o ChatGPT la sigan exactamente, porque la documentación de Codex no fue accesible |
| O-02 | Estructura de plugin de Codex: `plugins/<nombre>/.codex-plugin/plugin.json` obligatorio; `skills/` opcional dentro del plugin | `openai/plugins` README | Verificado |
| O-03 | Metadatos de interfaz y política de invocación en `agents/openai.yaml` | Búsqueda web sobre la documentación de Codex (no verificada directamente) | [No verificado] |
| O-04 | `AGENTS.md` como instrucciones de repositorio | No se obtuvo fuente oficial accesible | [No verificado] |
| O-05 | Requisitos específicos de skills dentro de ChatGPT | No se obtuvo fuente oficial accesible | [No verificado] |

## Aplicación a este repositorio

- `skills/auditor/SKILL.md` cumple la estructura del estándar abierto (O-01, verificado en el estándar).
- El adaptador de ChatGPT (`plataformas/chatgpt/`) no incluye manifiesto de plugin. Ver `docs/decisiones/20261019-adaptador-chatgpt-sin-manifiesto.md`.

## Estado del cumplimiento

Para el informe de auditoría, los requisitos O-03, O-04 y O-05 quedan como `NO_VERIFICADO` con la justificación de esta tabla, hasta que una consulta posterior a la documentación oficial sea posible.
