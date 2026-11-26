# Criterios de auditoría de octubre y su estado en dlc.audit

Origen: criterios C1 a C12 (versión 0.1.0, 2026-10-19) y taxonomía de la rama `claude/gallant-babbage-2srymf`, portados el 2026-11-26. Este documento no es el catálogo de reglas (`rules/*.json`, que es lo que se aplica) sino la **trazabilidad** de aquellos criterios hacia el diseño actual: qué cumple cada uno, con qué mecanismo y qué falta.

Estados: **Vigente** (se cumple igual), **Adaptado** (se cumple de otra forma), **Reemplazado** (la decisión cambió), **Parcial** y **No implementado** (hay una brecha).

## Criterios

| # | Criterio de octubre | Estado | Cómo se cumple hoy | Brecha o cambio |
|---|---|---|---|---|
| C1 | Independencia: los criterios residen en el auditor; los archivos del repositorio auditado son objeto de auditoría, no guía | Vigente | `AGENTS.md` reglas 6 (el contenido auditado es dato) y 8 (solo reglas de `rules/`); el catálogo vive en este repositorio | Ninguna |
| C2 | Solo lectura sobre el código auditado; sin credenciales | Adaptado | No se modifica nada del repositorio auditado salvo crear y, al cerrar el ciclo, borrar ramas `audit/*`; no se ejecuta su código (`AGENTS.md` regla 2; guardianes de `publish` y `cleanup`) | Hoy sí se usa el permiso de escritura del usuario para empujar ramas de auditoría. "Sin credenciales" ya no se cumple a la letra |
| C3 | Única escritura: informe en `auditorias/` por rama y PR; informes anteriores no se reescriben | Reemplazado | Los informes no se guardan (`decisiones/20261126-sin-informes-en-este-repositorio.md`); el informe vive en una rama `audit/*` transitoria que se borra al aprobar | Cambio deliberado; ver `decisiones/20261019-respuestas-preguntas-abiertas.md` |
| C4 | Evidencia reproducible: archivo y línea, SHA completo del commit y comando o lectura que la sustenta | Parcial | `validate` comprueba cada cita `ruta:línea` y extracto literal contra el archivo; `target.revision` es el SHA completo | No se registra el comando o la lectura que produjo cada hallazgo |
| C5 | Requisitos oficiales con fuente, URL, fecha y versión; si no es accesible, `NO_VERIFICADO` | Parcial | `docs/cumplimiento/` (citas literales, URL, fecha y estado). Las reglas con fuente externa llevan `requirements` hacia esos IDs y una prueba verifica que existan y estén verificados | 31 de 44 reglas contrastadas; las 13 restantes (`TRN-001`, `SKL-005`, `SKL-012`, `SQL-006`, `SQL-007`, `SQL-010` a `SQL-012`, `PYT-001` a `PYT-004` y `PYT-007`) se apoyan en buenas prácticas generales (OWASP, PEP 8, Oracle) que no se han releído. Las fuentes no publican versión |
| C6 | Separar hechos de inferencias: **[Inferencial]** y **[No verificado]** | Vigente | `confidence`: `verified`, `inferential`, `unverified` (`docs/contrato-salida.md`); los no verificados no bloquean el dictamen | Ninguna |
| C7 | Contradicciones: dos afirmaciones con sus fuentes, alcance e implicaciones, sin proponer la corrección | Parcial | Regla de juicio `TRN-008`: pide registrar cada afirmación con su fuente, el alcance y las implicaciones | Es una regla de juicio: `validate` comprueba la evidencia pero no que el hallazgo tenga la estructura de dos afirmaciones. No hay detección determinista |
| C8 | Seguimiento solo contra una auditoría previa válida; IDs estables | Parcial | Los `id` son huellas estables sin números de línea; `closure` y `reaudit` comparan contra el baseline publicado en la rama `audit/<run_id>` | El baseline no se vuelve a validar antes de usarse ni se firma: quien pueda escribir en esa rama podría alterarlo **[Inferencial]**. `cleanup` solo comprueba la forma de la rama al borrarla |
| C9 | Mínima exposición: sin secretos ni datos personales en el informe | Parcial | `TRN-001` redacta todas las credenciales de una línea; la rama publicada y los prompts no contienen valores; hay pruebas. `TRN-009` (juicio) busca datos personales y exige evidencia redactada | Los datos personales dependen del juicio del agente: no hay detector determinista |
| C10 | Estado por requisito oficial (`CUMPLE`, `NO_CUMPLE`, `NO_APLICA`, `NO_VERIFICADO`); `NO_CUMPLE` lleva a `FAIL` | Adaptado | El informe incluye la sección "Cumplimiento de requisitos oficiales": por cada requisito vinculado a una regla, el estado se calcula con esas reglas (hallazgo: `NO_CUMPLE`; regla pendiente o requisito no verificado: `NO_VERIFICADO`; todas no aplicables: `NO_APLICA`; evaluadas sin hallazgos: `CUMPLE`) | `NO_CUMPLE` no fuerza el dictamen: este sigue la severidad de los hallazgos. 24 de los 47 requisitos no tienen regla vinculada porque describen cómo cada plataforma carga las skills, no una propiedad auditable de un repositorio |
| C11 | Formato del informe validado antes de publicar (`validar_informe.py`) | Reemplazado | `validate --final` valida estructura, catálogo, evidencia y reglas pendientes; `render` genera el informe y los prompts desde el JSON | El formato YAML y su validador no se portan (`multiplataforma.md`, M3) |
| C12 | Sincronía de adaptadores byte a byte con el origen | Vigente | `python -m dlc_audit skills check`; `tests/test_skills.py` falla si una copia se edita a mano | Los adaptadores son `.claude/skills/` y `.agents/skills/` |

## Taxonomía

### Categorías de hallazgo

El esquema actual no tiene campo de categoría: el dominio de la regla (`transversal`, `skills-agentes`, `sql-plsql`, `python`) y el `change_group` cumplen ese papel.

| Categoría de octubre | Equivalente hoy |
|---|---|
| `seguridad` | `TRN-001`, `SKL-007`, `SKL-008`, `SKL-012`, `SQL-006`, `SQL-007`, `SQL-012`, `PYT-003`, `PYT-004`, `PYT-007` |
| `formato` | `SKL-002`, `SKL-004`, `SKL-009`, `SKL-013` a `SKL-015`, `SQL-001` a `SQL-004` |
| `calidad` | `SKL-003`, `SKL-005`, `SKL-011`, `TRN-005`, `TRN-006` |
| `trazabilidad` | `SQL-009`, `TRN-003` |
| `cumplimiento` | `SKL-001` a `SKL-004`, `SKL-006` a `SKL-009`, `SKL-013` a `SKL-016` y la matriz de cumplimiento (C10) |
| `contradiccion` | `TRN-008` |
| `independencia` | Sin regla: es una propiedad del auditor, no de lo auditado |
| `adaptador` | Sin regla sobre repositorios auditados; el auditor lo verifica en sí mismo con `skills check` |

### Severidades

Coinciden: `critico` = `critical`, `alto` = `high`, `medio` = `medium`, `bajo` = `low`, `informativo` = `info`.

### Estados de hallazgo

| Octubre | Hoy |
|---|---|
| `NUEVO` | Nuevo (sección de comparación del informe) |
| `ABIERTO` | Persistente |
| `CERRADO` | Resuelto |
| `SIN_CAMBIO` | Sin equivalente: la huella ignora las líneas, así que no distingue un hallazgo sin cambios de uno con evidencia modificada |

El campo `status` de un hallazgo vale `open` en Fase 1.

## Brechas que siguen abiertas

- C4: registrar el comando o la lectura que sustenta cada hallazgo.
- C8: validar el baseline antes de usarlo.
- C5: contrastar con su fuente las 13 reglas restantes.
- C7 y C9: sin detección determinista.

Las dos primeras están en la Fase 2 del roadmap y las otras, como trabajo futuro del catálogo, en los pendientes de `alcance.md`.
