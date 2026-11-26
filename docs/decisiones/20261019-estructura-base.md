# 2026-10-19 Estructura base del repositorio

Estado: Reemplazada

Origen: rama `claude/gallant-babbage-2srymf` (octubre de 2026), portada el 2026-11-26.

## Contexto

La especificación de la sección 5 define la estructura de `dlc.audit`. El repositorio estaba vacío.

## Decisión

Se crea la estructura de la sección 5 sin cambios: `README.md`, `CHANGELOG.md`, `AGENTS.md`, `skills/`, `plataformas/`, `docs/` (metodología, cumplimiento, decisiones), `plantillas/`, `referencias/<repositorio-auditado>/`, `scripts/` y `tests/`.

## Motivo

Es la estructura que Diego pidió. Cambiarla sin razón obliga a revisarla de nuevo.

## Consecuencias

- `auditorias/` no se crea aquí. Pertenece a cada repositorio auditado.

## Vigencia en dlc.audit (2026-11-26)

La estructura vigente está en `README.md`. No existen `plataformas/`, `plantillas/`, `referencias/` ni `auditorias/`: las skills viven en `skills/` con copias generadas, y este repositorio no guarda informes (`20261126-sin-informes-en-este-repositorio.md`).
