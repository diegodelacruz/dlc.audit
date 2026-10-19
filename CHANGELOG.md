# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Unreleased]

### Añadido

- Estructura base del repositorio (`README.md`, `AGENTS.md`, `CHANGELOG.md`).
- Skill `skills/auditor/` como origen único.
- Adaptadores generados para Claude, ChatGPT y Antigravity en `plataformas/`.
- Criterios de auditoría `docs/metodologia/CRITERIOS.md` v0.1.0 y taxonomía `docs/metodologia/TAXONOMIA.md`.
- Documentos de cumplimiento en `docs/cumplimiento/` para OpenAI, Anthropic, Google y plataformas, con URL, fecha de consulta y estado.
- Especificación del formato de informe `docs/formato-informe.md` (v1.0) y plantilla `plantillas/informe-auditoria.md`.
- Validador `scripts/validar_informe.py` y validador `scripts/validar_adaptadores.py` (con `--regenerar`).
- Pruebas `unittest` en `tests/`, con fixtures de informe válido y mal formado.
- Registro de decisiones en `docs/decisiones/`.
- Plantilla de repositorios auditables `docs/repositorios.md`.

### Pendiente

- Material de `apex.skills` en `referencias/apex-skills/` (no recibido).
- Verificación de requisitos de ChatGPT y de Antigravity (documentación no accesible en la sesión de creación).
