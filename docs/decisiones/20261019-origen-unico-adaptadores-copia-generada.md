# 2026-10-19 Origen único con adaptadores como copia generada

Estado: aceptada (pendiente de revisión por Diego)

## Contexto

La especificación exige un origen único en `skills/` y adaptadores por plataforma sin duplicar contenido. Diego trabaja en Windows 11, donde los enlaces simbólicos no son fiables para clonados ni para instalación manual.

## Opciones consideradas

1. **Enlaces simbólicos** desde `plataformas/` hacia `skills/`. Sin duplicación real, pero frágiles en Windows.
2. **Adaptador con referencia** (un `SKILL.md` que dice "lee `../../skills/auditor/SKILL.md`"). Sin duplicación, pero la skill instalada fuera del repositorio no encuentra su contenido.
3. **Copia generada** desde `skills/` con `scripts/validar_adaptadores.py --regenerar`, y verificación por hash con `scripts/validar_adaptadores.py`.

## Decisión

Opción 3. Los adaptadores son copias byte a byte generadas por script. Nadie los edita a mano; el validador detecta cualquier desvío.

## Motivo

Es la única que funciona instalada fuera del repositorio y en Windows. La duplicación queda controlada por la verificación, no por la disciplina de quien edita.

## Consecuencias

- El contenido aparece dos veces en el repositorio, pero solo una vez de forma editable.
- Cualquier cambio en `skills/` exige ejecutar `--regenerar` antes de commitear. El validador falla si se olvida.
