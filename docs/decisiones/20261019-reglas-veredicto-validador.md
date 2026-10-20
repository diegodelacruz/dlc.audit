# 2026-10-19 Reglas de veredicto implementadas en el validador

Estado: aceptada (pendiente de revisión por Diego)

## Contexto

La especificación define `FAIL` por "una validación obligatoria no ejecutada" y `PASS` por "todos los controles aplicables pasan", pero no dice si un control `FAIL` obliga a `FAIL`, ni qué controles son obligatorios.

## Decisión

El validador aplica estas reglas:

- Obligan a `FAIL`: un hallazgo crítico o alto sin cerrar, un proveedor `NO_CUMPLE`, un control `FAIL` y un control `NO_EJECUTADO`.
- `PASS` no admite: hallazgos medios sin cerrar, controles `N/A`, ni proveedores `NO_VERIFICADO`.
- `PASS_WITH_NA` exige al menos un control `N/A`.

Un control `NO_EJECUTADO` se trata como validación obligatoria no ejecutada. No se distingue entre obligatorio y opcional en v1.

## Motivo

Es la lectura más estricta que no contradice el texto. Permite un `PASS` solo cuando todo lo aplicable se comprobó.

## Consecuencias

- Un informe con un control `NO_EJECUTADO` no puede ser `PASS`. Si Diego quiere distinguir controles opcionales, hay que añadir esa marca al formato (versión 1.1).
