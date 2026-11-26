# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Unreleased]

## [0.3.1] - 2026-11-26

### Corregido

- `TRN-001`: si una línea contenía varias credenciales, solo se redactaba la primera y las demás llegaban al informe. Ahora se redactan todas y hay una evidencia por línea.
- `publish`: ya no publica archivos sueltos de la carpeta del run; solo `hallazgos.json`, `informe.md`, `prompt-integrador.md` y `prompts/*.md`.
- `fetch`: rechaza reutilizar `work/<nombre>` si el origen es otro repositorio con el mismo nombre.
- Datos no confiables hacia git: `ref`, SHAs del cierre del integrador y `baseline_run_id` leídos de ramas remotas se validan antes de usarse (evita inyección de opciones).
- Pruebas de endurecimiento (`tests/test_hardening.py`).

## [0.3.0] - 2026-11-26

### Añadido

- Cierre del ciclo: `cleanup` archiva los registros y elimina del remoto las ramas `audit/*` del ciclo aprobado (cadena por `baseline_run_id`), con simulación por defecto, dictamen `APROBADO` obligatorio y rechazo de ramas que contengan algo distinto de `.audit/<run_id>/`.
- `merge-prompt`: prompt autosuficiente para que el integrador integre la rama aprobada; se detiene si la rama tiene commits no auditados o si la rama principal avanzó; estrategia configurable (`merge` del perfil).
- Las skills preguntan al usuario si genera el prompt de merge; no lo generan sin respuesta afirmativa.
- Pruebas del cierre de ciclo (archivado, borrado acotado, rama manipulada, rama ajena, dictamen no aprobado).

### Cambiado

- `run_id` incluye segundos y, desde la ronda 2, el número de ronda (`...-r2-...`): evita colisiones entre rondas consecutivas.
- Regla inviolable 1 de `AGENTS.md`: únicas escrituras remotas permitidas = crear y, al cerrar el ciclo, borrar ramas `audit/<run_id>`.
- Perfil `default` v1.2.0 (`merge`).

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
