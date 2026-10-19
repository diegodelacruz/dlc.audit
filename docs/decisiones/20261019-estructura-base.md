# 2026-10-19 Estructura base del repositorio

Estado: aceptada

## Contexto

La especificación de la sección 5 define la estructura de `dlc.audit`. El repositorio estaba vacío.

## Decisión

Se crea la estructura de la sección 5 sin cambios: `README.md`, `CHANGELOG.md`, `AGENTS.md`, `skills/`, `plataformas/`, `docs/` (metodología, cumplimiento, decisiones), `plantillas/`, `referencias/apex-skills/`, `scripts/` y `tests/`.

## Motivo

Es la estructura que Diego pidió. Cambiarla sin razón obliga a revisarla de nuevo.

## Consecuencias

- `auditorias/` no se crea aquí. Pertenece a cada repositorio auditado.
