# Alcance y fases

## Qué hace dlc.audit

Audita un repositorio objetivo en **solo lectura** y entrega:

| Entregable | Archivo | Uso |
|---|---|---|
| Informe de auditoría | `informe.md` | Lectura humana |
| Hallazgos estructurados | `hallazgos.json` | Trazabilidad, comparación entre auditorías |
| Prompts de cambio | `prompts/NN-<grupo>.md` + `prompts/INDEX.md` | Se pegan en Claude Code, dentro del repositorio auditado |

## Dominios (Fase 1)

| Dominio | Qué cubre | Catálogo |
|---|---|---|
| `transversal` | Secretos, documentación, higiene, pruebas, hardcode de entorno | `rules/transversal.json` |
| `skills-agentes` | `SKILL.md`, subagentes, hooks, permisos | `rules/skills-agentes.json` |
| `sql-plsql` | SQL, PL/SQL y APEX: convenciones, seguridad, idempotencia | `rules/sql-plsql.json` |
| `python` | Python, FastAPI, AWS Glue | `rules/python.json` |

## Fuera de alcance (Fase 1)

- Modificar el repositorio auditado o generar diffs aplicables.
- Ejecutar el código auditado, sus tests o conectarse a bases de datos o a AWS.
- Análisis de datos reales, rendimiento en tiempo de ejecución, pruebas de penetración.
- Informes `.docx`/`.xlsx`/`.pdf`.
- Integración con CI y comentarios automáticos en PR.
- Dominios no listados (Power BI, JDE, MongoDB).

## Roadmap

| Fase | Contenido | Definition of Done |
|---|---|---|
| 1 | Núcleo: scan, validate, render, 4 catálogos, agente y skills | Tests pasan; auditoría de punta a punta sobre un repositorio real sin errores de `validate --final` |
| 2 | Re-auditoría con baseline, estados de hallazgo (aceptado, falso positivo) con aprobación | Un hallazgo cerrado se reconcilia entre runs sin duplicarse |
| 3 | Salida SARIF, ejecución en CI | Definir cuando se decida |

## Decisiones tomadas

| Decisión | Valor |
|---|---|
| Forma de ejecución | Agente Claude Code + skills, con núcleo determinista en Python |
| Modo sobre el objetivo | Solo lectura estricta |
| Formatos | `.md`, `.json`, prompts `.md` |
| Almacenamiento de resultados | `audits/<repo>/<run_id>/`, ignorado por git (puede contener información sensible) |

## Pendientes de definición [No verificado]

- Si `audits/` debe versionarse en un repositorio privado aparte para trazabilidad histórica.
- Umbrales de severidad que bloquean una entrega (cuando exista CI).
- Lista de excepciones aprobadas por proyecto (mecanismo de supresión con aprobación).
