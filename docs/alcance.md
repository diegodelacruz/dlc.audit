# Alcance y fases

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
- Fusionar o limpiar ramas `audit/*`.
- Ejecutar el código auditado, sus tests o conectarse a bases de datos o a AWS.
- Análisis de datos reales, rendimiento en tiempo de ejecución, pruebas de penetración.
- Informes `.docx`/`.xlsx`/`.pdf`.
- Integración con CI y comentarios automáticos en PR.
- Comunicación directa auditor-integrador: el usuario traslada los dos prompts de cada ronda.
- Dominios no listados (Power BI, JDE, MongoDB).

## Roadmap

| Fase | Contenido | Definition of Done |
|---|---|---|
| 1 | Núcleo, protocolo de dos rondas (fetch, publish, closure), 4 catálogos, agente y skills | Tests pasan; un ciclo completo sobre un repositorio real termina con dictamen sin errores de `validate --final` |
| 2 | Estados de hallazgo (riesgo aceptado, falso positivo) con aprobación y mecanismo de supresión; limpieza de ramas `audit/*` | Un hallazgo suprimido no reaparece entre rondas y queda trazado quién lo aprobó |
| 3 | Salida SARIF, ejecución en CI | Definir cuando se decida |

## Decisiones tomadas

| Decisión | Valor |
|---|---|
| Forma de ejecución | Agente Claude Code + skills, con núcleo determinista en Python |
| Modo sobre el objetivo | No modifica el código. Única escritura: rama nueva `audit/<run_id>` con archivos bajo `.audit/<run_id>/` (guardián en `publish`). Reemplaza la decisión inicial de "solo lectura estricta" porque el flujo exige una rama con las observaciones |
| Formatos | `.md`, `.json`, prompts `.md` |
| Entrada | Enlace del repositorio (URL https/ssh) y rama o commit opcional |
| Conversación | Cada prompt indica `MISMA` o `NUEVA`; ambos son autosuficientes |
| Almacenamiento de resultados | `audits/<repo>/<run_id>/`, ignorado por git (puede contener información sensible) |

## Pendientes de definición [No verificado]

- Permiso de escritura en los repositorios auditados (necesario para publicar la rama).
- Si `audits/` debe versionarse en un repositorio privado aparte para trazabilidad histórica.
- Umbrales de severidad que bloquean una entrega (cuando exista CI).
- Lista de excepciones aprobadas por proyecto (mecanismo de supresión con aprobación).
