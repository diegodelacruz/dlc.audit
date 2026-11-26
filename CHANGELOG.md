# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Unreleased]

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
