# 2026-10-19 Validador sin dependencias externas

Estado: aceptada

## Contexto

Diego usa Python desde python.org en Windows 11, no Anaconda. Las dependencias externas (PyYAML, pytest) pueden no estar instaladas.

## Decisión

`scripts/validar_informe.py` y `scripts/validar_adaptadores.py` usan solo la biblioteca estándar. El parser lee el subconjunto de YAML del formato (pares clave-valor y un nivel de mapa). Las pruebas usan `unittest`.

## Motivo

Un validador que requiere instalar paquetes se salta por comodidad. Con biblioteca estándar, el mismo comando funciona en cualquier equipo.

## Consecuencias

- El parser no acepta YAML general (listas anidadas, anclas, multilínea). El formato lo prohíbe; el validador rechaza lo que no entiende.
