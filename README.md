# dlc.audit

Auditor independiente de repositorios. Revisa otro repositorio en **solo lectura** y entrega:

- `informe.md`: informe de auditoría con hallazgos, severidad, certeza y evidencia (`archivo:línea`).
- `hallazgos.json`: fuente de verdad, con identificadores estables para comparar auditorías.
- `prompts/`: prompts de cambio listos para pegar en Claude Code dentro del repositorio auditado.

dlc.audit **no corrige** el repositorio auditado. Las correcciones las ejecutas tú con los prompts generados.

## Qué audita (Fase 1)

| Dominio | Ejemplos de reglas |
|---|---|
| Transversal | Secretos, README, CHANGELOG, `.gitignore`, pruebas y CI, valores fijos de entorno |
| Skills y agentes de Claude | Frontmatter, nombres, descripciones, herramientas del subagente, permisos, enlaces rotos |
| SQL, PL/SQL y APEX | Formato, SQL dinámico, `when others then null`, idempotencia, auditoría, parametrización |
| Python, FastAPI, Glue | Dependencias, excepciones, SQL interpolado, rutas S3 fijas, llamadas peligrosas |

El catálogo completo está en `rules/*.json` (38 reglas). Qué queda fuera: `docs/alcance.md`.

## Requisitos

- Python 3.11 o superior (python.org). Sin dependencias externas.
- Git en el `PATH`.
- Claude Code, para las skills y el subagente.

## Uso

### Con Claude Code (recomendado)

Abre Claude Code en este repositorio y pide:

```
/audit-repo C:\ruta\al\repositorio-objetivo
```

La skill ejecuta el flujo completo. Tras aplicar los prompts de cambio en el objetivo:

```
/reaudit C:\ruta\al\repositorio-objetivo audits\<repo>\<run>\hallazgos.json
```

### Manual

```
python -m dlc_audit scan <objetivo> --out audits/<repo>/<run>/hallazgos.json
# evaluar reglas pending (agente dlc-auditor) y completar executive_summary
python -m dlc_audit validate audits/<repo>/<run>/hallazgos.json --assign-ids
python -m dlc_audit validate audits/<repo>/<run>/hallazgos.json --final
python -m dlc_audit render audits/<repo>/<run>/hallazgos.json
```

`scan` por sí solo ya entrega los hallazgos deterministas. Las reglas de juicio quedan en `pending` hasta que el agente las evalúe; `render` no genera entregables de un run que no pase `validate --final`.

## Garantías de diseño

- **Solo lectura** sobre el objetivo: `scan` no escribe en él y las reglas del agente lo prohíben.
- **Evidencia verificada:** `validate` comprueba que cada cita exista en el archivo real; una cita inventada se rechaza.
- **Certeza explícita:** `verified`, `inferential` (**[Inferencial]**), `unverified` (**[No verificado]**).
- **Secretos redactados** en informe y prompts.
- **Idempotente:** mismo objetivo y revisión producen los mismos ids de hallazgo.
- **Parametrizado:** reglas versionadas y con vigencia en `rules/`; perfiles en `profiles/`.

## Estructura

```
AGENTS.md                reglas para agentes
docs/                    alcance, contrato de salida, metodología
rules/                   catálogos de reglas (JSON, versionados)
profiles/                perfiles: catálogos, severidades, convenciones de prompts
templates/               plantillas de informe y prompts
dlc_audit/               scan, validate, render (Python, solo biblioteca estándar)
.claude/agents/          subagente dlc-auditor
.claude/skills/          audit-repo, reaudit
tests/                   pruebas (unittest)
audits/                  resultados (ignorado por git)
```

## Pruebas

```
python -m unittest discover -s tests
```

## Documentación

- [Alcance y fases](docs/alcance.md)
- [Contrato de salida](docs/contrato-salida.md)
- [Metodología](docs/metodologia.md)
- [Changelog](CHANGELOG.md)
