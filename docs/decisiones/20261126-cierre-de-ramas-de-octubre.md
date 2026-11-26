# 2026-11-26 Cierre del PR de octubre y destino de las ramas antiguas

Estado: aceptada

## Contexto

Al empezar la sesión había tres ramas abiertas: la de este trabajo, `claude/gallant-babbage-2srymf` (PR #1, diseño paralelo de octubre) y `claude/nice-carson-yc8xgi` (informes de auditoría de otro repositorio, sin PR). El usuario decidió el portado selectivo de la primera y descartar la segunda.

## Decisión

1. El contenido útil de la rama de octubre se portó en los PR #5, #6 y #7. El PR #1 se cierra sin fusionar, con un comentario que explica qué se portó, qué no y por qué.
2. La rama `claude/nice-carson-yc8xgi` se descarta: este repositorio no guarda informes de auditoría (`20261126-sin-informes-en-este-repositorio.md`). Su último commit es `acee29172f5ebac5b59dd6734384a0eefcd83297`.
3. El usuario borra las ramas a mano: la sesión de trabajo recibe un 403 del servidor al borrar ramas o crear etiquetas.
4. **Recuperación de la rama de octubre:** no se pudo crear una etiqueta de archivo, pero GitHub conserva la cabeza de cada PR en `refs/pull/<n>/head`. Se comprobó que `refs/pull/1/head` es `9c56eefb2c52d46ad85be7702d58c0b7b5fe362d`, idéntico a la rama, y se recupera con `git fetch origin refs/pull/1/head`.

## Motivo

La rama de octubre y la actual resolvían el mismo problema con arquitecturas incompatibles; portar lo útil evita mantener dos. La referencia de PR cumple el propósito de la etiqueta sin necesitar permisos que la sesión no tiene.

## Consecuencias

- La rama `claude/nice-carson-yc8xgi` no tiene PR, así que **no** deja referencia recuperable más allá de su SHA mientras GitHub conserve los objetos sin referencia.
- El borrado de las tres ramas antiguas queda en manos del usuario.
