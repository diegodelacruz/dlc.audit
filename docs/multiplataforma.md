# Multiplataforma (bloque 1: definición)

Estado: **aceptada el 2026-11-26** por el usuario. Bloques 2 a 4 implementados; bloque 5 preparado, a la espera de la prueba del usuario (ver al final).

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

## Plataformas (consulta literal del 2026-11-26)

Las citas textuales, las URL y el estado de cada requisito están en [`cumplimiento/`](cumplimiento/plataformas.md).

| Plataforma | Dónde carga las skills | Estado de verificación |
|---|---|---|
| Claude Code | `.claude/skills/<nombre>/SKILL.md` (A-05) | **Verificado** en texto completo. Todos los campos del frontmatter son opcionales y los desconocidos se ignoran, pero la subida a claude.ai o a la API falla con error ante cualquier campo fuera de su lista (A-06, A-07) |
| Codex | `.agents/skills/` desde el directorio actual hasta la raíz del repositorio (O-02). `name` y `description` obligatorios (O-01) | **Verificado** en texto completo. Recomienda las carpetas directas de skill para flujos acotados al repositorio y presenta el plugin como mecanismo de distribución (O-06). Sin límites de longitud (O-04); sandbox, permisos, red y git no documentados |
| Antigravity | `<raíz>/.agents/skills/<skill>/SKILL.md` en App, CLI e IDE, y carpetas padre hasta la raíz (G-02). `description` obligatoria; `name` opcional (G-01) | **Verificado** en texto completo. Las skills pueden incluir scripts ejecutables (G-04); terminal, red y git no documentados |
| ChatGPT | Subida desde *Skills, Create, Upload from your computer* (O-08), con escaneo previo (O-09). Planes Business, Enterprise, Healthcare y Edu (O-07) | Subida **verificada**. Formato de archivo, ejecución, red, GitHub y `git push` **no documentados** (O-08, O-11) |

Límites de esta verificación: Antigravity y ChatGPT no publican versión; ninguna página de Codex ni de ChatGPT muestra fecha (la de ChatGPT dice "Updated: last month"); el último tercio de la página de Claude Code llegó como resumen y no se usó. Detalle en cada archivo de `cumplimiento/`.

**Correcciones a la primera versión de este documento** (el mismo día, tras la relectura literal): el plugin de Codex no se declara "innecesario"; la documentación recomienda las carpetas directas para este caso y presenta el plugin como mecanismo de distribución. Y la razón para dejar solo `name` y `description` no es solo la falta de documentación de Codex y Antigravity: la subida a claude.ai y a la API **rechaza** los campos fuera de su lista (A-07).

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
- **ChatGPT:** `python -m dlc_audit skills package` genera un `.zip` con una carpeta por skill, escrito en el directorio temporal y nunca en este repositorio. El formato de subida de ChatGPT no está documentado: es el empaquetado habitual del estándar y consta como **[No verificado]**.
- **El plugin de Codex y el manifiesto de ChatGPT de la rama de octubre no se portan.** Quedan reemplazados por esta decisión; el plugin es un mecanismo de distribución (O-06), lo que M1 deja fuera de v1.

### Reglas de portabilidad de `skills/`

1. Frontmatter solo con `name` y `description`. Nada de `argument-hint` ni campos propietarios: la subida a claude.ai y a la API falla con error ante campos fuera de su lista (A-07) y Codex y Antigravity no documentan qué hacen con campos desconocidos. La especificación abierta admite cuatro campos opcionales más (S-04); no se usan.
2. `name` en minúsculas, números y guiones, de hasta 64 caracteres, igual al nombre de su carpeta y sin las palabras "claude" ni "anthropic" (restricción de Anthropic).
3. `description` no vacía, de hasta 1.024 caracteres y sin etiquetas XML (Anthropic). Debe decir qué hace y cuándo usarla.
4. Sin variables ni herramientas propietarias (`$ARGUMENTS`, `AskUserQuestion`, `.claude/`). Se redacta en términos generales con alternativa: "si la plataforma ofrece una herramienta para preguntar con opciones, úsala; si no, pregunta en texto y espera".
5. Rutas relativas a la raíz de la skill (`references/...`). El procedimiento detallado vive en `references/`; el `SKILL.md` se mantiene breve.
6. El procedimiento de evaluación de reglas de juicio se escribe una vez en `references/` y lo leen tanto la skill como el subagente opcional de Claude Code.

## Alcance de la implementación

| Bloque | Contenido | Estado |
|---|---|---|
| 1 | Esta definición | Aceptada |
| 2 | Fuente única `skills/`, generador y validador de sincronía (`skills check` y `skills sync`), portabilidad de las dos skills, comando `skills package` | **Hecho** |
| 3 | Portado desde `claude/gallant-babbage-2srymf`: `docs/cumplimiento/` releído de forma literal, `docs/decisiones/` saneadas, criterios C1 a C12 como trazabilidad en `criterios.md` | **Hecho** |
| 4 | Catálogo de reglas: reglas enlazadas con `docs/cumplimiento/` (`requirements`), `source_verified` contrastado, reglas nuevas (`SKL-013` a `SKL-016`, `TRN-008`, `TRN-009`) y matriz de cumplimiento en el informe | **Hecho** |
| 5 | Cierre del PR #1 y de las ramas de octubre; guion y repositorio de demostración para la prueba de punta a punta | **PR #1 cerrado; borrado de ramas y prueba real pendientes del usuario** (`prueba-extremo-a-extremo.md`) |

## Definition of Done de v1 (plataformas)

1. El validador de sincronía pasa y las copias coinciden con `skills/`.
2. `docs/cumplimiento/` registra fuente, URL y fecha por plataforma.
3. **Claude Code:** el usuario completó un ciclo real de punta a punta (L2), siguiendo `prueba-extremo-a-extremo.md`. **Pendiente.**
4. Codex, Antigravity y ChatGPT: instalación documentada (L1); su ejecución consta como **[No verificado]** hasta que alguien la pruebe.
