# Alcance y fases

## Estado de v1

**v1 NO está completa.** La decisión de octubre (2026-10-19) hacía obligatorias Claude, Codex, ChatGPT y Antigravity. El 2026-11-26 se redefinió qué significa "soportada": **instalable en las 4 plataformas, con ejecución probada donde se pueda probar**. Como el usuario solo puede probar Claude Code, solo Claude Code puede quedar verificado de punta a punta; las demás constan como **[No verificado]** en ejecución. Definición, matriz de plataformas, reglas de portabilidad y plan por bloques: [multiplataforma.md](multiplataforma.md).

Lo implementado hoy cubre solo Claude Code (skills `audit-repo` y `reaudit`, subagente `dlc-auditor`) sobre un núcleo Python independiente de la plataforma.

Pendiente para cerrar v1: que el usuario ejecute la prueba de punta a punta en Claude Code (`prueba-extremo-a-extremo.md`) y borre a mano las ramas antiguas (`decisiones/20261126-cierre-de-ramas-de-octubre.md`). El contenido útil de la rama `claude/gallant-babbage-2srymf` (PR #1) ya está portado (bloque 3); la rama se conserva hasta el bloque 5.

## Qué hace dlc.audit

Actúa como **auditor externo** en un flujo integrador-auditor (ver `protocolo.md`). Recibe el enlace de un repositorio, no modifica su código y entrega:

| Entregable | Archivo | Uso |
|---|---|---|
| Informe de auditoría | `informe.md` | Lectura humana |
| Hallazgos estructurados | `hallazgos.json` | Trazabilidad, comparación entre auditorías |
| Prompt del integrador | `prompt-integrador.md` | Único prompt que se pega en el integrador; incluye la plantilla de cierre |
| Prompts de detalle | `prompts/NN-<grupo>.md` + `prompts/INDEX.md` | El integrador los lee de la rama `audit/<run_id>` y los ejecuta en orden |
| Rama de auditoría | `audit/<run_id>` en el repositorio auditado | Canal de transporte; nunca se fusiona |

## Dominios (Fase 1)

| Dominio | Qué cubre | Catálogo |
|---|---|---|
| `transversal` | Secretos, documentación, higiene, pruebas, hardcode de entorno | `rules/transversal.json` |
| `skills-agentes` | `SKILL.md`, subagentes, hooks, permisos | `rules/skills-agentes.json` |
| `sql-plsql` | SQL, PL/SQL y APEX: convenciones, seguridad, idempotencia | `rules/sql-plsql.json` |
| `python` | Python, FastAPI, AWS Glue | `rules/python.json` |

## Fuera de alcance (Fase 1)

- Modificar el código del repositorio auditado o generar diffs aplicables.
- Ejecutar el merge (lo hace el integrador con el prompt de merge) o borrar ramas que no sean `audit/*` de un ciclo aprobado.
- Ejecutar el código auditado, sus tests o conectarse a bases de datos o a AWS.
- Análisis de datos reales, rendimiento en tiempo de ejecución, pruebas de penetración.
- Informes `.docx`/`.xlsx`/`.pdf`.
- **Guardar informes de auditoría en este repositorio**, bajo cualquier forma (versionados, archivados o en disco).
- Integración con CI y comentarios automáticos en PR.
- Comunicación directa auditor-integrador: el usuario traslada los dos prompts de cada ronda.
- Dominios no listados (Power BI, JDE, MongoDB).

## Roadmap

| Fase | Contenido | Definition of Done |
|---|---|---|
| 1 | Núcleo, protocolo de dos rondas (fetch, publish, closure), 4 catálogos, agente y skills | Tests pasan; un ciclo completo sobre un repositorio real termina con dictamen sin errores de `validate --final` |
| 2 | Estados de hallazgo (riesgo aceptado, falso positivo) con aprobación y mecanismo de supresión | Un hallazgo suprimido no reaparece entre rondas y queda trazado quién lo aprobó |
| 3 | Salida SARIF, ejecución en CI | Definir cuando se decida |

## Decisiones tomadas

| Decisión | Valor |
|---|---|
| Forma de ejecución | Agente Claude Code + skills, con núcleo determinista en Python |
| Modo sobre el objetivo | No modifica el código. Únicas escrituras: crear ramas `audit/<run_id>` con archivos bajo `.audit/<run_id>/` (guardián en `publish`) y borrar las de un ciclo aprobado (guardián en `cleanup`). Reemplaza la decisión inicial de "solo lectura estricta" porque el flujo exige una rama con las observaciones |
| Formatos | `.md`, `.json`, prompts `.md` |
| Entrada | Enlace del repositorio (URL https/ssh) y rama o commit opcional |
| Conversación | Cada prompt indica `MISMA` o `NUEVA`; ambos son autosuficientes. Confirmado por el usuario |
| Dictamen | `critical`, `high` y `medium` bloquean; los no verificados no. Confirmado por el usuario |
| Cierre del ciclo | Al aprobar: borrar ramas `audit/*` del ciclo y preguntar al usuario si genera el prompt de merge. Confirmado por el usuario |
| Almacenamiento de resultados | **Ninguno en este repositorio.** Archivos de trabajo en el directorio temporal del sistema, purgados al cerrar el ciclo; el informe final solo en la conversación. Decisión del usuario, 2026-11-26 |

## Decisiones de la sesión 2026-11-26

| Decisión | Valor |
|---|---|
| Plataformas v1 | Instalable en Claude Code, Codex, ChatGPT y Antigravity; ejecución probada donde se pueda (hoy solo Claude Code). Ver `multiplataforma.md` |
| Formato del informe | El actual (JSON y documentos generados); se descarta el formato YAML de la rama de octubre |
| Modo de uso de las skills | Dentro de un clon de `dlc.audit` |
| Rama `claude/gallant-babbage-2srymf` (PR #1) | Portado selectivo y luego cierre del PR y borrado de la rama, con etiqueta de archivo |
| Rama `claude/nice-carson-yc8xgi` | Descartada por el usuario (contenía informes de auditoría de otro repositorio; último commit `acee291`) |
| Método de merge a `main` | Merge commit (`--no-ff`) |
| Secuencia | Fusionar el núcleo ahora con v1 marcado incompleto; la multiplataforma se construye después |

## Pendientes de definición [No verificado]

- Permiso de escritura en los repositorios auditados (publicar y borrar ramas `audit/*`).
- Si el integrador debe eliminar su rama de corrección tras el merge (hoy: solo si la creó exclusivamente para la auditoría).
- Cómo conservar, si se necesita, la trazabilidad de una auditoría sin guardar informes en este repositorio (hoy: ninguna; solo perdura lo que quede en el repositorio auditado).
- Umbrales de severidad que bloquean una entrega (cuando exista CI).
- Lista de excepciones aprobadas por proyecto (mecanismo de supresión con aprobación).
