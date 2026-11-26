# 2026-11-26 Multiplataforma: alcance y modo de uso

Estado: aceptada

## Contexto

La rama `claude/gallant-babbage-2srymf` (PR #1, octubre) decidió que Claude, Codex (prioridad), ChatGPT y Antigravity eran obligatorias en v1, con skills instalables fuera del repositorio, adaptadores de plugin y un formato de informe en YAML. El auditor actual cubre solo Claude Code y guarda sus informes de forma transitoria, nunca en este repositorio. La documentación oficial de Codex, Antigravity y ChatGPT, inaccesible en octubre, se pudo leer el 2026-11-26.

## Decisión

1. Modo de uso dentro de un clon de `dlc.audit`; sin empaquetar el núcleo en las copias.
2. "Soportada" en v1 significa instalable en las 4 plataformas, con ejecución probada donde se pueda.
3. Se mantiene el formato de informe actual (JSON y documentos generados).
4. El usuario solo puede probar Claude Code de punta a punta.

## Motivo

Dos carpetas (`.claude/skills/` y `.agents/skills/`) cubren Claude Code, Codex y Antigravity con el estándar abierto Agent Skills. Empaquetar el núcleo en cada plataforma duplicaría unas 2.000 líneas sin necesidad mientras se trabaje desde un clon. El validador de informes de octubre no tiene objeto cuando no se almacenan informes.

## Consecuencias

- Solo Claude Code puede quedar verificado de punta a punta en v1; el resto consta como **[No verificado]** en ejecución. Esto relaja la decisión del 2026-10-19.
- El adaptador de plugin de Codex y el manifiesto de ChatGPT de octubre quedan reemplazados y no se portan.
- ChatGPT exige un plan Business, Enterprise, Healthcare o Edu con Skills habilitadas, y su capacidad de ejecutar Python o hacer `git push` no está documentada.

Detalle y plan de implementación: `docs/multiplataforma.md`.
