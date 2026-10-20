# Cumplimiento: Google

Fecha de consulta: **2026-10-19**.

## Fuentes consultadas

| Fuente | URL | Resultado |
|---|---|---|
| Antigravity: skills (documentación oficial) | https://antigravity.google/docs/skills | **No accesible** (proxy 403) |
| Antigravity: codelab (Google Developers) | https://codelabs.developers.google.com/getting-started-with-antigravity-skills | **No accesible** (sin conexión) |
| Gemini CLI: GEMINI.md (documentación en el repositorio oficial) | https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/gemini-md.md | Accesible |
| Resultados de búsqueda sobre Antigravity | Varias URL de terceros y de copias localizadas del sitio oficial | Indicativas, **no verificadas** |

## Requisitos

| ID | Requisito | Fuente | Estado |
|---|---|---|---|
| G-01 | Gemini CLI carga archivos de contexto llamados `GEMINI.md` desde el directorio global `~/.gemini/`, desde el espacio de trabajo y sus padres, y de forma just-in-time al acceder a archivos | Gemini CLI, `gemini-md.md` | Verificado (Gemini CLI, no Antigravity) |
| G-02 | Antigravity: skills en `.agents/skills/<nombre>/SKILL.md`, con `description` obligatoria y `name` opcional | Solo fuentes secundarias | [No verificado] |
| G-03 | Antigravity: reglas (rules) y flujos (workflows) como archivos markdown en `.agents/rules` y de invocación con barra | Solo un tutorial de terceros | [No verificado] |
| G-04 | Antigravity: versión de la documentación | Copias localizadas citan versiones distintas (2.1.1, 2.5.2, 2.5.4) | [No verificado] |

## Aplicación a este repositorio

- El adaptador de Antigravity (`plataformas/antigravity/`) reproduce el origen en `.agents/skills/auditor/SKILL.md`, siguiendo G-02. Como G-02 no está verificado, el adaptador queda marcado como tal en `plataformas.md`.
- Para Gemini CLI, el adaptador no se genera: no hay requisito verificado de skills para esa herramienta en esta versión de la auditoría.

## Estado del cumplimiento

G-02, G-03 y G-04 quedan como `NO_VERIFICADO` en cualquier informe, con justificación de esta tabla.
