# 2026-11-26 Protocolo auditor-integrador

Estado: aceptada

## Contexto

El usuario trabaja con dos roles: un agente integrador construye y corrige repositorios; un auditor externo, aislado, valida el resultado sin ser juez y parte. El intercambio entre ambos lo traslada el usuario y debe ser mínimo sin omitir pasos.

## Decisión

1. El auditor recibe el enlace de un repositorio, lo audita y publica una rama `audit/<run_id>` con las observaciones (solo archivos bajo `.audit/<run_id>/`). Esa rama nunca se fusiona.
2. Cada ronda cuesta dos pegados: el prompt del integrador (con plantilla de cierre prellenada) y el cierre que el integrador devuelve. Cada prompt indica `CONVERSACIÓN: MISMA` o `NUEVA`, configurable en `handoff`.
3. El cierre del integrador se verifica contra el repositorio; cada ronda audita todo de nuevo.
4. Dictamen configurable en `approval`: `critical`, `high` y `medium` bloquean; los no verificados no.
5. Con `APROBADO`: se borran las ramas `audit/*` del ciclo, se pregunta al usuario si genera el prompt de merge y se purgan los archivos de trabajo. El merge lo ejecuta el integrador, nunca el auditor.
6. El auditor no modifica nada del repositorio auditado salvo crear y, al cerrar el ciclo, borrar ramas `audit/*`.

## Motivo

Mantiene la independencia del auditor, minimiza el intercambio de mensajes y deja el repositorio auditado sin restos de la auditoría.

## Consecuencias

- Requiere permiso de escritura en el repositorio auditado. En una sesión en la nube, el borrado de ramas puede ser denegado por política (403); entonces `cleanup` falla y el usuario las borra a mano.
- Detalle y garantías: `docs/protocolo.md`.
