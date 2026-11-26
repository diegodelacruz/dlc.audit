# 2026-11-26 Este repositorio no guarda informes de auditoría

Estado: aceptada

## Contexto

El diseño inicial escribía por defecto los informes en `audits/` dentro de este repositorio y `cleanup` los archivaba antes de borrar las ramas de auditoría. Además, dos ramas antiguas contenían informes de otro repositorio. El usuario confirmó que un repositorio auditor no debe guardarlos.

## Decisión

No se guardan informes de auditoría en este repositorio **bajo ningún concepto**: ni versionados, ni en ramas, ni en su disco. Los archivos de trabajo van al directorio temporal del sistema y `purge` los elimina al cerrar el ciclo. El informe final solo existe en la conversación; mientras dura el ciclo, también en la rama `audit/<run_id>` del repositorio auditado.

## Motivo

Un auditor que acumula informes de otros repositorios concentra información sensible (hallazgos de seguridad, rutas, historial) y deja de ser un instrumento para ser un archivo.

## Consecuencias

- Barrera en el código (`PolicyError`): `scan`, `fetch`, `render`, `closure`, `merge-prompt`, `skills package` y `save_json` rechazan rutas dentro del repositorio.
- `tests/test_no_reports.py` falla si se versiona algo con aspecto de informe o si un ciclo completo escribe en el repositorio.
- No queda ningún registro tras cerrar un ciclo; lo perdurable es lo que quede en el repositorio auditado (commits de corrección y merge del integrador).
- Las fixtures de pruebas y los documentos usan repositorios ficticios.
