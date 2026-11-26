# Multiplataforma (bloque 1: definición)

Estado: **aceptada el 2026-11-26** por el usuario. Implementación pendiente (bloques 2 a 5, al final).

## Decisiones

| # | Decisión | Valor |
|---|---|---|
| M1 | Modo de uso | Dentro de un clon de `dlc.audit`. La plataforma descubre las skills del propio repositorio y `python -m dlc_audit` está siempre disponible. No se empaqueta el núcleo Python en las copias |
| M2 | Qué es "soportada" en v1 | Instalable en las 4 plataformas; ejecución probada donde se pueda probar |
| M3 | Formato del informe | El nuestro: JSON como fuente de verdad, informe y prompts generados, dictamen APROBADO/NO APROBADO. Se descarta el formato YAML en español y el validador de informes de la rama `claude/gallant-babbage-2srymf`: no se guardan informes, así que no hay informes almacenados que validar |
| M4 | Plataformas que el usuario puede probar de punta a punta | **Solo Claude Code** |

Consecuencia de M2 y M4: **solo Claude Code puede quedar verificado de punta a punta en v1.** Codex, Antigravity y ChatGPT quedan instalables, con su ejecución marcada **[No verificado]** hasta que alguien la pruebe. Esto relaja la decisión del 2026-10-19 ("obligatorias en v1") y el usuario lo aceptó al elegir M2 y M4.

## Niveles de soporte

| Nivel | Significado | Cómo se demuestra |
|---|---|---|
| L1 Instalable | La plataforma descubre y carga las skills | Estructura conforme a la documentación oficial y validador de sincronía de copias |
| L2 Ejecutable | El ciclo completo (auditar, publicar, re-auditar, cerrar) funciona en esa plataforma | Prueba real de punta a punta sobre un repositorio |

## Plataformas (consulta del 2026-11-26)

| Plataforma | Dónde carga las skills | Fuente | Estado de verificación |
|---|---|---|---|
| Claude Code | `.claude/skills/<nombre>/SKILL.md` | Documentación de Anthropic | Verificado el 2026-10-19 en la rama de octubre; **se vuelve a leer al portar `docs/cumplimiento/`** |
| Codex | `.agents/skills/` desde el directorio actual hasta la raíz del repositorio; usuario `$HOME/.agents/skills`; administrador `/etc/codex/skills`. El plugin (`.codex-plugin/plugin.json`) **no es necesario** para usar una skill dentro de un repositorio | https://learn.chatgpt.com/docs/build-skills (destino de la redirección permanente desde https://developers.openai.com/codex/skills) | **Parcial.** Lectura asistida por un resumen generado por modelo, no texto literal. `name` y `description` obligatorios. Sin límites de longitud, sandbox, red ni git en lo leído |
| Antigravity | `<raíz>/.agents/skills/<skill>/SKILL.md` en App, CLI e IDE, y carpetas padre hasta la raíz del repositorio; global `~/.gemini/config/skills/`. `.agent/skills` sigue siendo compatible | https://antigravity.google/docs/skills.md | **Verificado en la página oficial** (sin fecha ni versión). `description` obligatoria; `name` opcional (por defecto, el nombre de la carpeta). Las skills pueden incluir scripts ejecutables. Declara seguir el estándar abierto Agent Skills. Sin límites de longitud, terminal, red ni git |
| ChatGPT | Subida desde *Skills, Create, Upload from your computer*, con escaneo previo (estados *Needs Review* y *Blocked*) | https://help.openai.com/en/articles/20001066-skills-in-chatgpt | Instalación **verificada**. Disponible para planes Business, Enterprise, Healthcare y Edu según la configuración del workspace. Formato de subida, entorno de ejecución, red, GitHub y `git push` **no documentados** en la página |

Límites de esta verificación: la fecha de consulta es la del encabezado; Antigravity y ChatGPT no publican fecha; el contenido de Codex proviene en parte de un resumen y debe releerse literalmente al portar `docs/cumplimiento/`.

## Requisitos del host

El flujo del auditor exige:

| Requisito | Obligatorio | Si falta |
|---|---|---|
| Shell y Python 3.11 o superior | Sí | La plataforma no puede ejecutar el flujo (solo L1) |
| Git con red y permiso de escritura en el repositorio auditado | Sí | No se puede clonar, publicar ni borrar ramas `audit/*` (solo L1) |
| Escritura en un directorio temporal fuera del repositorio | Sí | La barrera de `dlc_audit` rechaza cualquier otra ruta |
| Subagentes | No | La skill ejecuta el procedimiento de evaluación ella misma |
| Preguntas al usuario con opciones | No | Se pregunta en texto plano y se espera la respuesta |

## Diseño

```
skills/                       # fuente única, editable, portable
	audit-repo/SKILL.md
	audit-repo/references/    # procedimiento detallado (divulgación progresiva)
	reaudit/SKILL.md
	reaudit/references/
.claude/skills/               # copia generada para Claude Code
.agents/skills/               # copia generada para Codex y Antigravity
.claude/agents/dlc-auditor.md # atajo opcional, solo Claude Code
```

- **Una fuente, copias generadas.** Nadie edita las copias; un validador compara hashes y falla si difieren (decisión heredada de la rama de octubre: Windows 11 no maneja bien los enlaces simbólicos).
- **ChatGPT:** un comando genera el `.zip` para subir, escrito en el directorio temporal y nunca en este repositorio.
- **El plugin de Codex y el manifiesto de ChatGPT de la rama de octubre no se portan.** Quedan reemplazados por esta decisión; sirven para distribuir fuera del repositorio, lo que M1 deja fuera de v1.

### Reglas de portabilidad de `skills/`

1. Frontmatter solo con `name` y `description`. Nada de `argument-hint` ni campos propietarios: el comportamiento de campos desconocidos no está documentado en Codex ni en Antigravity.
2. `name` en minúsculas, números y guiones, de hasta 64 caracteres, igual al nombre de su carpeta y sin las palabras "claude" ni "anthropic" (restricción de Anthropic).
3. `description` no vacía, de hasta 1.024 caracteres y sin etiquetas XML (Anthropic). Debe decir qué hace y cuándo usarla.
4. Sin variables ni herramientas propietarias (`$ARGUMENTS`, `AskUserQuestion`, `.claude/`). Se redacta en términos generales con alternativa: "si la plataforma ofrece una herramienta para preguntar con opciones, úsala; si no, pregunta en texto y espera".
5. Rutas relativas a la raíz de la skill (`references/...`). El procedimiento detallado vive en `references/`; el `SKILL.md` se mantiene breve.
6. El procedimiento de evaluación de reglas de juicio se escribe una vez en `references/` y lo leen tanto la skill como el subagente opcional de Claude Code.

## Alcance de la implementación

| Bloque | Contenido | Estado |
|---|---|---|
| 1 | Esta definición | Aceptada |
| 2 | Fuente única `skills/`, generador y validador de sincronía, portabilidad de las dos skills, comando del `.zip` de ChatGPT | Pendiente |
| 3 | Portado desde `claude/gallant-babbage-2srymf`: `docs/cumplimiento/` releído y actualizado, `docs/decisiones/` saneadas con repositorios ficticios, criterios C1 a C12 como referencia | Pendiente |
| 4 | Catálogo de reglas: marcar `source_verified` con fuente en las reglas ya verificadas; nuevas comprobaciones de `name` ("claude" y "anthropic") y etiquetas XML | Pendiente |
| 5 | Cierre del PR #1 y borrado de la rama de octubre con etiqueta de archivo; prueba de punta a punta en Claude Code por el usuario | Pendiente |

## Definition of Done de v1 (plataformas)

1. El validador de sincronía pasa y las copias coinciden con `skills/`.
2. `docs/cumplimiento/` registra fuente, URL y fecha por plataforma.
3. **Claude Code:** el usuario completó un ciclo real de punta a punta (L2).
4. Codex, Antigravity y ChatGPT: instalación documentada (L1); su ejecución consta como **[No verificado]** hasta que alguien la pruebe.
