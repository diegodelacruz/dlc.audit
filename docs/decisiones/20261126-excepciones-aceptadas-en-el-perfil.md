# 2026-11-26 Excepciones aceptadas en el perfil del auditor

Estado: aceptada

## Contexto

Un hallazgo puede ser real pero aceptado por el propietario (por ejemplo, archivos grandes que son fixtures o upstreams vendorizados). Sin un mecanismo, reaparece en cada ronda y bloquea o ensucia el informe.

## Decisión

Las excepciones se declaran en `profiles/<perfil>.json`, clave `accepted_exceptions`, con `repo`, `rule_id`, `paths`, `reason`, `approved_by`, `valid_from` y `valid_to`. `scan` omite los hallazgos cubiertos por completo y declara cada excepción usada en `limitations` y `coverage.accepted_exceptions`.

## Motivo

- Parametrización primero, con vigencia y aprobador (trazabilidad).
- Viven en el auditor y no en el repositorio auditado: el objetivo no puede excusarse a sí mismo (principio 6 de AGENTS.md).
- No son informes: no contienen hallazgos ni resultados de un run, solo la política aceptada.
- No se ocultan en silencio: el informe indica cuántos hallazgos quedaron cubiertos y por qué (principio 9).

## Consecuencias

- Una excepción cubre solo la misma regla y rutas que coincidan con sus globs; un archivo nuevo fuera de los globs sí se informa.
- Cambiar una excepción incrementa la `version` del perfil.
- No cubre hallazgos de reglas de juicio añadidos por el agente; este debe respetar la lista de `coverage.accepted_exceptions`.
- `tests/test_docs.py` prohíbe nombrar repositorios auditados reales en archivos versionados. Por eso las excepciones concretas usan `repo: "*"` y se acotan por regla y globs de ruta; usar el nombre del repositorio queda reservado a nombres ficticios.
