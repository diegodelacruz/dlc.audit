# Contrato de salida

Versión del contrato: `1.0` (campo `schema_version`). Las claves JSON van en inglés; los textos, en español.

## Estructura de carpetas de una auditoría

```
audits/<repo>/<run_id>/
	hallazgos.json     # fuente de verdad
	informe.md         # generado
	prompts/
		INDEX.md
		01-<grupo>.md
```

`run_id` = `YYYYMMDDTHHMMZ-<repo>`.

## Documento del run (`hallazgos.json`)

| Campo | Tipo | Descripción |
|---|---|---|
| `schema_version` | string | `1.0` |
| `run_id` | string | Identificador único del run |
| `auditor` | objeto | `name`, `version`, `revision` (commit de dlc.audit) |
| `profile` | objeto | `name`, `version` |
| `target` | objeto | `name`, `path`, `revision` (commit auditado), `dirty` (bool) |
| `started_at`, `finished_at` | string ISO 8601 UTC | Marcas de tiempo |
| `coverage` | objeto | `files_total`, `files_by_domain`, `excluded` |
| `rules` | lista | Estado de cada regla del perfil (ver abajo) |
| `executive_summary` | string | Lo redacta el agente; obligatorio en `--final` |
| `limitations` | lista de string | Qué no se revisó y por qué |
| `findings` | lista | Hallazgos |

### `rules[]`

| Campo | Valores |
|---|---|
| `id`, `version` | Regla y versión aplicada |
| `method` | `deterministic` (la evalúa `scan`) o `judgment` (la evalúa el agente) |
| `status` | `evaluated`, `not_applicable`, `pending` |
| `note` | Motivo si `not_applicable` |

En `--final` no puede quedar ninguna regla en `pending`.

### `findings[]`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | `<RULE>-<huella>`; estable entre runs (ver Huella) |
| `rule_id`, `rule_version` | string | Debe existir en el catálogo |
| `severity` | enum | `critical`, `high`, `medium`, `low`, `info` |
| `confidence` | enum | `verified`, `inferential`, `unverified` |
| `title` | string | Corto |
| `description` | string | Qué ocurre y por qué importa |
| `evidence` | lista | Al menos una (ver abajo) |
| `recommendation` | string | Qué cambiar |
| `effort` | enum | `S` (< 1 h), `M` (< 1 día), `L` (> 1 día) |
| `change_group` | string | Agrupa hallazgos en un mismo prompt de cambio |
| `detected_by` | enum | `scan` o `agent` |
| `status` | enum | `open` en Fase 1 |

### `evidence[]`

| Campo | Descripción |
|---|---|
| `type` | `file` (cita de código) o `absence` (algo que debería existir y no existe) |
| `path` | Ruta relativa al repositorio objetivo, con `/` |
| `line_start`, `line_end` | Solo `file` |
| `excerpt` | Solo `file`: texto literal de esas líneas (se compara sin espacios) |
| `redacted` | `true` si el extracto oculta un secreto; no se compara el texto |
| `note` | Opcional |

## Severidad

| Nivel | Criterio |
|---|---|
| `critical` | Compromiso inmediato: secreto expuesto, ejecución arbitraria, inyección explotable |
| `high` | Riesgo serio de seguridad, pérdida de datos o fallo silencioso |
| `medium` | Deuda que degrada mantenibilidad, trazabilidad o resiliencia |
| `low` | Convención, higiene |
| `info` | Observación sin acción obligatoria |

## Certeza (`confidence`)

| Valor | Marca en el informe | Cuándo |
|---|---|---|
| `verified` | Verificado | La evidencia demuestra el hallazgo sin interpretación |
| `inferential` | **[Inferencial]** | Detección heurística o juicio apoyado en la evidencia |
| `unverified` | **[No verificado]** | Sospecha que requiere confirmar con el equipo; se reporta, no se prioriza |

`verified` exige evidencia que `validate` haya comprobado contra el archivo real.

## Huella (identificador estable)

`id = <rule_id>-<sha1(rule_id | type | path | extracto normalizado)[:10]>` usando la **primera** evidencia. No incluye números de línea, así que sobrevive a cambios de posición. Sirve para reconciliar runs: un `id` presente en el baseline y ausente ahora se considera **resuelto**.

Dos hallazgos de la misma regla con el mismo archivo y extracto colisionan; `validate` lo rechaza.

## Reglas del catálogo (`rules/*.json`)

| Campo | Descripción |
|---|---|
| `id`, `version` | `DOM-NNN`, SemVer |
| `title`, `description` | Qué se verifica y por qué |
| `domain` | `transversal`, `skills-agentes`, `sql-plsql`, `python` |
| `applies_to` | `["*"]` o lista de dominios que deben estar presentes en el objetivo |
| `severity`, `effort` | Valores por defecto (el perfil puede sobrescribir severidad) |
| `method`, `detector` | `deterministic` + función de `scan`, o `judgment` |
| `remediation`, `acceptance` | Qué cambiar y cuándo se considera corregido (alimenta los prompts) |
| `valid_from`, `valid_to` | Vigencia; `valid_to: null` = abierta |
| `source`, `source_verified` | Origen; `false` si el criterio no se ha contrastado con la fuente |

## Perfil (`profiles/<nombre>.json`)

Selecciona catálogos, deshabilita reglas, sobrescribe severidades, define exclusiones por glob y las convenciones que se inyectan en los prompts de cambio por dominio.
