# 2026-11-27 Evidencia `file_size` para TRN-007 y forma de `out_of_scope_changes`

Estado: aceptada

## Contexto

1. TRN-007 (archivo de más de 1 MB) emitía evidencia `absence` sobre un archivo que existe. El validador rechazaba ese hallazgo ("se declara ausencia pero <ruta> existe" y "'verified' exige evidencia comprobada"). Tampoco podía usar `file`, que exige líneas y extracto.
2. La plantilla del cierre imprimía `"out_of_scope_changes": []` sin la forma de cada entrada. Los integradores usaron `file` y `commit`; `closure` leía solo `path`, y emitía avisos falsos de deriva.

## Decisión

- Nuevo tipo de evidencia `file_size` con `path`, `size_bytes` (entero) y `note` opcional. `validate` exige que el archivo exista, que `size_bytes` sea entero (no booleano) y que coincida con el tamaño real; solo entonces la evidencia cuenta como comprobada. `d_large_files` lo emite con el tamaño real y conserva la limitación "no se analizó el contenido". El informe y los prompts muestran ruta, tamaño legible y nota.
- La plantilla del cierre incluye un ejemplo `{"path": ..., "reason": ...}` y la regla correspondiente. `closure` acepta `file` como alias de `path` (gana `path` si vienen ambos) con aviso informativo; entradas sin ruta, sin `reason` o que no son objetos generan aviso y nunca excepción.

## Motivo

- Alterar `absence` para admitir archivos existentes debilitaría una comprobación útil (detecta ausencias falsas). Un tipo propio mantiene cada tipo con una semántica verificable.
- Ser tolerante con `file` evita falsos avisos sin renunciar a la forma canónica, que el prompt ahora enseña.

## Consecuencias

- Ids de TRN-007: `finding_id` usa tipo, ruta y extracto. El tipo pasa de `absence` a `file_size` y no hay extracto, así que los ids de TRN-007 cambian respecto a versiones anteriores del auditor. Un baseline anterior mostrará esos hallazgos como resueltos y nuevos en una re-auditoría. El id sigue siendo estable entre ejecuciones de esta versión (no depende del tamaño).
- La regla TRN-007 no cambia de definición (mismo umbral, severidad y remediación), solo el formato de evidencia que emite su detector. Por eso conserva la versión `1.0.0`.
- Esquema: se amplía `evidence.type` de forma compatible hacia atrás para quien lee; un lector que solo conozca `file` y `absence` fallaría con `file_size`. No se incrementa `schema_version`: [Inferencial] no se conocen lectores externos del JSON.
- Las excepciones aceptadas por ruta no existen todavía en este repositorio (no hay `accepted_exceptions` ni `apply_exceptions`); cuando se implementen, comparar `ev["path"]` funciona con `file_size` porque el campo `path` es común a los tres tipos.
