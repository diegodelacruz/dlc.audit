# 2026-10-19 Recursos de la skill empaquetados dentro de skills/auditor/

Estado: Parcialmente vigente

Origen: rama `claude/gallant-babbage-2srymf` (octubre de 2026), portada el 2026-11-26.

## Contexto

La revisión de Codex en el PR #1 (hilo P1 sobre `skills/auditor/SKILL.md`) señaló que una instalación con solo `SKILL.md` no puede ejecutar el procedimiento: lo necesita leer `CRITERIOS.md`, `TAXONOMIA.md` y el formato del informe, que vivían en `docs/` de `dlc.audit`.

Diego eligió empaquetar esos recursos dentro de la skill.

## Decisión

- La fuente de `CRITERIOS.md`, `TAXONOMIA.md` y del formato vive en `skills/auditor/references/` (`CRITERIOS.md`, `TAXONOMIA.md`, `FORMATO-INFORME.md`).
- `SKILL.md` las referencia con rutas relativas a la raíz de la skill (`references/...`).
- `docs/metodologia/*.md` y `docs/formato-informe.md` son punteros a esa fuente. No duplican contenido.
- `scripts/validar_adaptadores.py` copia y verifica la carpeta completa de cada skill, no solo `SKILL.md`. Un archivo faltante o sobrante en un adaptador se reporta.

## Motivo

Una skill instalada fuera del repositorio debe funcionar sola. Así cada plataforma recibe los mismos criterios que el origen, y la verificación de sincronía cubre también los recursos.

## Consecuencias

- Cambiar criterios o formato obliga a regenerar adaptadores (`--regenerar`).
- Las rutas de `docs/cumplimiento/` y de las decisiones que citaban `docs/formato-informe.md` siguen válidas como punteros.

## Vigencia en dlc.audit (2026-11-26)

Se mantiene que el detalle de una skill vive dentro de su carpeta (`skills/audit-repo/references/`). Ya no se mantiene el motivo "una skill instalada fuera del repositorio debe funcionar sola": las skills se usan dentro de un clon de `dlc.audit` (decisión M1 de `docs/multiplataforma.md`).
