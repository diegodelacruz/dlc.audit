# Taxonomía

Versión de referencia: criterios 0.1.0 (ver `CRITERIOS.md` en esta misma carpeta).

## Categorías de hallazgo

El ID de cada hallazgo tiene la forma `HALL-<categoría>-<hash>`, donde `<categoría>` está en minúsculas, con guiones si hace falta.

| Categoría | Qué cubre |
|---|---|
| `seguridad` | Secretos, credenciales, permisos excesivos, instrucciones que piden ejecutar acciones peligrosas |
| `independencia` | Dependencia del auditado para definir criterios o aceptar hallazgos |
| `formato` | Estructura de skills, frontmatter, nombres y límites de campos |
| `cumplimiento` | Incumplimiento de un requisito oficial de OpenAI, Anthropic o Google |
| `trazabilidad` | Falta de SHA, fuentes, fechas o versiones |
| `contradiccion` | Afirmaciones enfrentadas dentro del repositorio o frente a su documentación |
| `adaptador` | Desincronía entre origen y adaptadores de plataforma |
| `calidad` | Ambigüedad, instrucciones contradictorias o inoperables |

## Severidades

| Severidad | Criterio |
|---|---|
| `critico` | Riesgo inmediato de exposición de secretos o de ejecución no autorizada, o incumplimiento que impide el uso en una plataforma |
| `alto` | Incumplimiento de un requisito oficial o contradicción que cambia el comportamiento esperado |
| `medio` | Desviación de criterios propios o formato que dificulta la verificación |
| `bajo` | Inconsistencia menor sin efecto sobre el comportamiento |
| `informativo` | Observación sin acción requerida |

## Estados de hallazgo

| Estado | Significado |
|---|---|
| `NUEVO` | Aparece por primera vez en esta auditoría |
| `ABIERTO` | Existía en la auditoría previa válida y sigue presente |
| `CERRADO` | Existía en la auditoría previa válida y ya no se observa |
| `SIN_CAMBIO` | Igual que en la auditoría previa, sin cambio de evidencia |

## Estados de control

`PASS`, `FAIL`, `N/A` (con justificación), `NO_EJECUTADO` (con razón).

## Estados de cumplimiento por proveedor

`CUMPLE`, `NO_CUMPLE`, `NO_APLICA`, `NO_VERIFICADO`.

## Veredictos

| Veredicto | Condición |
|---|---|
| `FAIL` | Hay un hallazgo crítico o alto sin resolver (estado distinto de `CERRADO`), o un requisito de proveedor `NO_CUMPLE`, o un control `FAIL`, o un control `NO_EJECUTADO` |
| `PASS_WITH_NA` | No hay críticos ni altos sin resolver, pero hay controles `N/A` justificados |
| `PASS` | Todos los controles aplicables pasan, no hay medios sin resolver y ningún requisito de proveedor queda `NO_VERIFICADO` sin justificar |

El validador comprueba que el veredicto declarado sea coherente con estas condiciones.
