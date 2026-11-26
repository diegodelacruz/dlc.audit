# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Unreleased]

## [0.2.0] - 2026-11-26

### Añadido

- Protocolo auditor-integrador en rondas de dos mensajes (`docs/protocolo.md`).
- `fetch`: clona por enlace con hooks de git desactivados y fija la revisión auditada.
- `publish`: crea la rama `audit/<run_id>` con archivos bajo `.audit/<run_id>/`; guardián que aborta si el diff toca otra ruta; sin force push; anonimiza la ruta local.
- `closure`: verifica el cierre del integrador contra el repositorio (commits, archivos, deriva, declaraciones contradichas).
- `prompt-integrador.md`: prompt único autosuficiente con plantilla de cierre prellenada e indicación `CONVERSACIÓN: MISMA|NUEVA`.
- Dictamen (`APROBADO`, `APROBADO CON OBSERVACIONES`, `NO APROBADO`) configurable en `approval` del perfil.
- Campos `round`, `baseline_run_id`, `target.url` y `target.ref` en el run.
- Pruebas del protocolo completo en dos rondas con un remoto git local.

### Cambiado

- Skills `audit-repo` (entrada por URL, publica la rama) y `reaudit` (parte del cierre del integrador).
- Regla inviolable 1 de `AGENTS.md`: el auditor no modifica el código; su única escritura es la rama de auditoría. Reemplaza "solo lectura estricta".
- Los prompts de detalle ya no se pegan uno a uno: el integrador los lee de la rama del auditor.
- Perfil `default` v1.1.0 (`approval`, `handoff`, exclusión de `.audit/`).

## [0.1.0] - 2026-11-26

### Añadido

- Núcleo `dlc_audit` (solo biblioteca estándar): `scan`, `validate`, `render`.
- Catálogos versionados con vigencia: transversal (7), skills y agentes (12), SQL/PL-SQL (12), Python (7).
- Perfil `default` con severidades y convenciones por dominio para los prompts de cambio.
- Validación de evidencia contra el archivo real, huella estable de hallazgos y control de reglas pendientes.
- Informe `.md` con comparación contra baseline y prompts de cambio agrupados por hallazgo.
- Subagente `dlc-auditor` y skills `audit-repo` y `reaudit`.
- Documentación: alcance, contrato de salida, metodología y `AGENTS.md`.
- Pruebas de extremo a extremo con `unittest`.
