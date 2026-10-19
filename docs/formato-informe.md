# Formato estándar del informe de auditoría

- Versión del formato: **1.0**
- Versión de criterios: **0.1.0** (`docs/metodologia/CRITERIOS.md`)
- Estado: **pendiente de revisión por Diego**

Este documento es la especificación que el validador `scripts/validar_informe.py` aplica.

## Ubicación

Cada auditoría produce un archivo dentro del repositorio auditado, en `auditorias/`:

```
auditorias/
├── INDICE.md                          # Una fila por informe
├── historial.csv                      # Serie para contraste
└── AAAA-MM-DD-NNN-<slug>.md           # Un informe por auditoría
```

- `AAAA-MM-DD-NNN`: fecha UTC de la auditoría y número de orden del día, con tres dígitos (`001`, `002`, ...).
- `<slug>`: minúsculas, dígitos y guiones. Por ejemplo `apex-skills`.
- Los informes nunca se reescriben. Una corrección se hace con un informe nuevo.

## Encabezado YAML (obligatorio)

El archivo empieza con un bloque YAML delimitado por `---`. Campos obligatorios:

| Campo | Tipo | Regla |
|---|---|---|
| `id` | texto | `AUD-AAAA-MM-DD-NNN`, coincide con la fecha y el número del nombre de archivo |
| `repositorio` | texto | `propietario/nombre` |
| `rama` | texto | Rama auditada |
| `commit_auditado` | texto | SHA completo de 40 caracteres hexadecimales |
| `fecha_utc` | texto | `AAAA-MM-DDTHH:MM:SSZ` |
| `auditor` | mapa | Campos `repositorio`, `commit_auditor` (SHA de 40 caracteres), `version_criterios`, `agente`, `plataforma_ejecucion` |
| `alcance` | texto | Qué se auditó y qué quedó fuera |
| `auditoria_previa` | texto o `null` | ID de un informe previo válido, o `null` |
| `veredicto` | texto | `PASS`, `PASS_WITH_NA` o `FAIL` |
| `conteo_hallazgos` | mapa | Enteros `critico`, `alto`, `medio`, `bajo`, `informativo` |

`plataforma_ejecucion` admite `ChatGPT`, `Claude` o `Antigravity`.

Ejemplo:

```yaml
id: AUD-2026-10-19-001
repositorio: diegodelacruz/apex.skills
rama: claude/beautiful-goldberg-gak8us
commit_auditado: 506ca81...   # SHA completo de 40 caracteres
fecha_utc: 2026-10-19T14:00:00Z
auditor:
  repositorio: diegodelacruz/dlc.audit
  commit_auditor: <SHA completo>
  version_criterios: 0.1.0
  agente: <nombre y versión>
  plataforma_ejecucion: Claude
alcance: skills/ y AGENTS.md de la raíz; fuera: scripts de PowerShell
auditoria_previa: null
veredicto: FAIL
conteo_hallazgos:
  critico: 0
  alto: 1
  medio: 0
  bajo: 0
  informativo: 0
```

## Cuerpo: secciones en este orden

Cada sección es un encabezado `## N. Nombre`. Si una sección no aplica, se escribe `N/A` con una justificación concreta.

1. **Resumen**: veredicto y los tres hallazgos más importantes.
2. **Entradas leídas**: archivos con su SHA; referencias externas con URL y fecha de consulta.
3. **Comandos ejecutados**: comando exacto, código de salida y resumen de salida.
4. **Controles**: tabla con columnas `Control | Resultado | Evidencia | Justificación`. `Resultado` admite `PASS`, `FAIL`, `N/A`, `NO_EJECUTADO`.
5. **Cumplimiento por proveedor**: tabla con columnas `Proveedor | Requisito | Fuente (URL y fecha) | Estado | Evidencia`. `Estado` admite `CUMPLE`, `NO_CUMPLE`, `NO_APLICA`, `NO_VERIFICADO`.
6. **Hallazgos**: un bloque por hallazgo, con el formato siguiente.
7. **Contradicciones**: afirmaciones enfrentadas, con fuentes, razón o historial verificable (o la declaración de que no se pudo determinar), alcance e implicaciones. Sin corrección propuesta.
8. **Seguimiento**: hallazgos cerrados, abiertos y nuevos frente a la auditoría previa válida.
9. **Limitaciones**: qué no se pudo verificar y por qué.

### Bloque de hallazgo

```markdown
### HALL-formato-3f9a21

- **Severidad:** alto
- **Categoría:** formato
- **Estado:** NUEVO
- **Evidencia:** skills/auditor/SKILL.md:4
- **Descripción:** ...
- **Implicación:** ...
```

- El ID sigue la forma `HALL-<categoría>-<hash>`. `<categoría>` está en minúsculas y `<hash>` tiene entre 6 y 12 caracteres hexadecimales, calculados sobre `archivo+regla`.
- `Severidad` admite `critico`, `alto`, `medio`, `bajo`, `informativo`.
- `Estado` admite `NUEVO`, `ABIERTO`, `CERRADO`, `SIN_CAMBIO`.
- El validador cuenta los bloques por severidad y los compara con `conteo_hallazgos`.

## Reglas de veredicto

- `FAIL` si hay un hallazgo crítico o alto con estado distinto de `CERRADO`, un requisito de proveedor `NO_CUMPLE`, un control `FAIL`, o un control `NO_EJECUTADO` (se trata como validación obligatoria no ejecutada; ver `docs/decisiones/20261019-reglas-veredicto-validador.md`).
- `PASS_WITH_NA` si no hay críticos ni altos sin cerrar, pero hay controles `N/A` justificados.
- `PASS` solo si todos los controles aplicables pasan, no hay medios sin cerrar y ningún requisito de proveedor queda `NO_VERIFICADO` sin justificar.

El validador rechaza un veredicto que contradiga estas reglas.

## Antecedentes y seguimiento

Una auditoría previa cuenta como antecedente solo si tiene un encabezado YAML válido y fue generada por este auditor. Las demás se listan como existentes, sin usarlas para el seguimiento.

## Índice e historial

Al cerrar cada informe se añade:

- Una fila a `auditorias/INDICE.md` con ID, fecha, commit, veredicto y enlace al informe.
- Una fila a `auditorias/historial.csv` con las columnas `id,fecha_utc,commit_auditado,veredicto,critico,alto,medio,bajo,informativo`.

## Flujo de publicación

1. Crear rama nueva en el repositorio auditado (por ejemplo `auditoria/AUD-2026-10-19-001`).
2. Escribir el informe, `INDICE.md` e `historial.csv`.
3. Ejecutar `scripts/validar_informe.py` sobre el informe.
4. Abrir pull request hacia `main`. No hacer merge: lo fusiona Diego.
