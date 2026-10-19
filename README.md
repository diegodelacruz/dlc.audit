# dlc.audit

Agente auditor independiente para repositorios de skills y agentes. Verifica su calidad y su cumplimiento frente a los requisitos oficiales de OpenAI, Anthropic y Google, y produce un informe `.md` por auditoría dentro del repositorio auditado.

`dlc.audit` es el lugar donde vive el agente. No es el repositorio auditado.

## Qué hace

1. Audita repositorios de skills y agentes (por ejemplo `diegodelacruz/apex.skills`).
2. Escribe un informe en `auditorias/` del repositorio auditado, por rama nueva y pull request.
3. Verifica el cumplimiento con documentación oficial consultada en la fecha de la auditoría.

## Plataformas

| Plataforma | Adaptador | Verificación |
|---|---|---|
| Claude | `plataformas/claude/skills/auditor/` | Verificado (documentación de Anthropic, 2026-10-19) |
| ChatGPT | `plataformas/chatgpt/skills/auditor/` | [No verificado]: documentación oficial no accesible |
| Antigravity | `plataformas/antigravity/.agents/skills/auditor/` | [No verificado]: solo fuentes secundarias |

Ver `docs/cumplimiento/plataformas.md`.

## Estructura

- `skills/`: origen único. Una carpeta por skill con `SKILL.md`.
- `plataformas/`: copias generadas del origen para cada plataforma.
- `skills/auditor/references/`: criterios (v0.1.0), taxonomía y formato del informe. Viajan con la skill; `docs/metodologia/` y `docs/formato-informe.md` apuntan ahí.
- `docs/cumplimiento/`: requisitos oficiales, con URL, fecha y estado.
- `plantillas/`: plantilla de informe.
- `scripts/`: validadores.
- `tests/`: pruebas de los validadores.

## Uso de los validadores

Con Python 3 instalado desde python.org (no requiere paquetes adicionales):

```
python -I -m unittest discover -s tests -v
python -I scripts/validar_informe.py <ruta-al-informe.md>
python -I scripts/validar_adaptadores.py
python -I scripts/validar_adaptadores.py --regenerar
```

`--regenerar` copia `skills/` a los adaptadores. Hay que ejecutarlo tras cualquier cambio en el origen.

## Límites

- v1 solo lee código. No corrige, no hace commit en el repositorio auditado y no usa credenciales.
- No ejecuta pruebas que requieran Oracle, credenciales o PowerShell de Windows.
- La escritura se hace por PR. Diego fusiona manualmente.
- El material de `referencias/apex-skills/` no ha llegado todavía. Ver `referencias/apex-skills/README.md`.

## Documentos

- `AGENTS.md`: reglas para cualquier agente que modifique este repositorio.
- `CHANGELOG.md`: historial de cambios.
- `docs/decisiones/`: una decisión por archivo.
- `docs/repositorios.md`: repositorios auditables.
