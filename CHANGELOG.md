# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Unreleased]

### Añadido

- Estructura base del repositorio (`README.md`, `AGENTS.md`, `CHANGELOG.md`).
- Skill `skills/auditor/` como origen único.
- Adaptadores generados para Claude, ChatGPT y Antigravity en `plataformas/`.
- Criterios de auditoría v0.1.0 y taxonomía, en `skills/auditor/references/`.
- Documentos de cumplimiento en `docs/cumplimiento/` para OpenAI, Anthropic, Google y plataformas, con URL, fecha de consulta y estado.
- Especificación del formato de informe (v1.0), en `skills/auditor/references/FORMATO-INFORME.md`, y plantilla `plantillas/informe-auditoria.md`.
- Validador `scripts/validar_informe.py` y validador `scripts/validar_adaptadores.py` (con `--regenerar`).
- Pruebas `unittest` en `tests/`, con fixtures de informe válido y mal formado.
- Registro de decisiones en `docs/decisiones/`.
- Plantilla de repositorios auditables `docs/repositorios.md`.

### Añadido (Codex)

- Adaptador de Codex como plugin en `plataformas/codex/`, con manifiesto `.codex-plugin/plugin.json` y verificación en `validar_adaptadores.py`. Ver `docs/decisiones/20261020-adaptador-codex-plugin.md`.

### Cambiado

- Criterios, taxonomía y formato del informe se empaquetan dentro de `skills/auditor/references/`. `docs/` apunta ahí. Ver `docs/decisiones/20261019-recursos-empaquetados-en-skill.md`.
- `scripts/validar_adaptadores.py` copia y verifica la carpeta completa de cada skill, incluido `references/`.
- `scripts/validar_informe.py` rechaza filas de tabla malformadas (antes se descartaban en silencio), campos obligatorios vacíos, hallazgos sin `Evidencia`, `Descripción` o `Implicación`, controles `N/A` sin justificación y requisitos `NO_APLICA` sin evidencia.

### Pendiente

- Material de `apex.skills` en `referencias/apex-skills/` (no recibido).
- Verificación de requisitos de ChatGPT y de Antigravity (documentación no accesible en la sesión de creación).
