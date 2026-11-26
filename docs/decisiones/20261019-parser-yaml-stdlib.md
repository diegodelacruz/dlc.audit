# 2026-10-19 Validador sin dependencias externas

Estado: Vigente (adaptada)

Origen: rama `claude/gallant-babbage-2srymf` (octubre de 2026), portada el 2026-11-26.

## Contexto

Diego usa Python desde python.org en Windows 11, no Anaconda. Las dependencias externas (PyYAML, pytest) pueden no estar instaladas.

## Decisión

`scripts/validar_informe.py` y `scripts/validar_adaptadores.py` usan solo la biblioteca estándar. El parser lee el subconjunto de YAML del formato (pares clave-valor y un nivel de mapa). Las pruebas usan `unittest`.

## Motivo

Un validador que requiere instalar paquetes se salta por comodidad. Con biblioteca estándar, el mismo comando funciona en cualquier equipo.

## Consecuencias

- El parser no acepta YAML general (listas anidadas, anclas, multilínea). El formato lo prohíbe; el validador rechaza lo que no entiende.

## Vigencia en dlc.audit (2026-11-26)

El núcleo de `dlc_audit` usa solo la biblioteca estándar y las pruebas usan `unittest`. El lector de frontmatter es `parse_frontmatter` en `dlc_audit/scan.py`. El validador de informes en YAML no se porta (ver `20261126-multiplataforma-alcance-y-modo.md`).
