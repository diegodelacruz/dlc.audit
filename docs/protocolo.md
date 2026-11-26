# Protocolo auditor-integrador

## Roles

| Rol | Quién | Hace | No hace |
|---|---|---|---|
| Integrador | Agente de Claude Code en el repositorio de trabajo | Construye, modifica y elimina. Corrige lo que el auditor observa | No audita su propio trabajo; no decide si un hallazgo es válido |
| Auditor | Este repositorio (`dlc.audit`) | Audita por enlace, publica observaciones, verifica el cierre y dictamina | No modifica nada del repositorio auditado salvo crear y, al cerrar, borrar ramas `audit/*` |
| Usuario | Tú | Traslada dos mensajes entre agentes | |

El auditor es externo y aislado para que el repositorio modificado no sea juez y parte.

## Ciclo (2 mensajes por ronda)

```
 Usuario            Auditor (dlc.audit)                      Integrador
    |  enlace            |                                        |
    |------------------->| fetch, scan, evaluación, validate      |
    |                    | render, publish audit/<run_id>         |
    |<-------------------| PROMPT A (para el integrador)          |
    |  PROMPT A          |                                        |
    |--------------------------------------------------------------->| lee la rama audit/<run_id>
    |                    |                                        | corrige en su rama, push
    |<---------------------------------------------------------------| PROMPT B = cierre (JSON)
    |  PROMPT B          |                                        |
    |------------------->| closure (verifica lo declarado)        |
    |                    | scan + evaluación completos de nuevo   |
    |                    | dictamen; si no aprueba: publish y     |
    |<-------------------| nuevo PROMPT A                         |
```

Termina con el dictamen `APROBADO`. Cada ronda cuesta exactamente dos pegados: A al integrador y B al auditor.

## Cierre del ciclo

Con dictamen `APROBADO`:

1. **Limpieza (automática):** el auditor elimina del remoto las ramas `audit/*` del ciclo. No guarda ningún registro. Las ramas se identifican siguiendo `baseline_run_id` desde el run final; no se borra ninguna otra. Antes de borrar cada una se comprueba que contiene únicamente `.audit/<run_id>/`; si alguien le añadió código, se rechaza y se informa.
2. **Pregunta al usuario:** ¿genera el prompt de merge a la rama principal?
3. **Purga:** al final, `purge` elimina de este equipo los archivos de trabajo (informes, prompts, clones). Es el último paso y solo se ejecuta después de la respuesta del usuario, para poder mostrar el informe final en la conversación si lo pide.
4. **Prompt C (merge), solo si se acepta:** lo ejecuta el integrador. Se detiene si la rama tiene commits posteriores a la auditoría o si la rama principal avanzó (el resultado del merge no habría sido auditado), no fuerza el push, y retira worktrees y ramas locales de la auditoría.

Con `APROBADO CON OBSERVACIONES` se pregunta antes: cerrar aceptándolas u otra ronda. Con `NO APROBADO` no se borra nada.

El auditor **no hace** el merge: no modifica nada del repositorio auditado.

## Los dos prompts

| | Prompt A (auditor al integrador) | Prompt B (integrador al auditor, "cierre") |
|---|---|---|
| Generado por | `render` en el auditor | El propio integrador, a partir de la plantilla incluida en A |
| Archivo | `.audit/<run_id>/prompt-integrador.md` | Se entrega en el chat |
| Contenido | Dictamen, tabla de hallazgos, pasos, plantilla de cierre prellenada con un id por hallazgo | Datos del repositorio y baseline, resumen, JSON de cierre (estado, commits, archivos, verificación por hallazgo) |
| Detalle completo | En la rama `audit/<run_id>` (evidencia, qué hacer, criterios de aceptación) | Se comprueba contra el repositorio |
| Conversación | Indicada en la cabecera: `MISMA` o `NUEVA` | Indicada en la cabecera: `MISMA` o `NUEVA` |

Ambos son **autosuficientes**: funcionan en la misma conversación o en una nueva. La cabecera `CONVERSACIÓN` indica cuál usar y por qué. El valor por defecto se define en `profiles/default.json`, clave `handoff`.

Requisito para el auditor en conversación nueva: abrir la sesión en el repositorio `dlc.audit`, donde están las skills.

## La rama del auditor

- Nombre: `audit/<run_id>`. Se crea a partir de la revisión auditada.
- Contenido: solo `.audit/<run_id>/` (`informe.md`, `hallazgos.json`, `prompt-integrador.md`, `prompts/`).
- **Nunca se fusiona.** Es un canal de transporte. El integrador la lee con `git worktree` o con herramientas de GitHub y trabaja en su propia rama.
- Una rama nueva por ronda; nunca se reutiliza ni se fuerza.
- El campo `target.path` se anonimiza (`(local)`) antes de publicar.

## Garantías de independencia

| Garantía | Mecanismo |
|---|---|
| El auditor no toca el código | `publish` crea la rama en un clon temporal y aborta si el diff contra la revisión auditada toca algo fuera de `.audit/<run_id>/` |
| La rama auditada no cambia | No hay push a ella; no hay force push |
| El borrado es acotado | `cleanup` solo borra ramas del ciclo con nombre `audit/<run_id>` y contenido exclusivo de `.audit/<run_id>/`; no archiva nada; el dictamen debe ser `APROBADO` |
| El auditor no cree al integrador | `closure` contrasta cada declaración (commits, archivos) con el repositorio |
| No se esconden cambios | Cualquier archivo cambiado que nadie declaró se reporta como **deriva** |
| No se declara lo no hecho | Un `fixed` cuyo hallazgo sigue detectándose se reporta como **contradicho** |
| El auditor no confía solo en el delta | Cada ronda es una auditoría completa, no solo de lo declarado |
| El integrador no puede contaminar el árbol auditado | La presencia de `.audit/` en su rama se reporta; `.audit/` se excluye del escaneo |

## Dictamen

Configurable en `profiles/default.json`, clave `approval`.

| Dictamen | Condición (valores por defecto) |
|---|---|
| `APROBADO` | Sin hallazgos |
| `APROBADO CON OBSERVACIONES` | Solo hallazgos `low` o `info`, o solo `unverified` |
| `NO APROBADO` | Algún hallazgo `critical`, `high` o `medium` que no sea `unverified` |

## Estados del cierre (`status`)

| Valor | Significado | Exige |
|---|---|---|
| `fixed` | Corregido | `commits`, `files`, `verification` |
| `not_applicable` | El integrador sostiene que no aplica | `note` con evidencia |
| `not_fixed` | No se corrigió | `note` con el motivo |
| `partial` | Corrección parcial | `note`, y `commits`/`files` de lo hecho |

La decisión sobre `not_applicable` y `not_fixed` es del auditor: si la evidencia no respalda al integrador, el hallazgo persiste.

## Riesgos y límites [Inferencial]

- **Permisos:** publicar la rama exige escritura en el repositorio auditado. Sin ella, el flujo se detiene antes de `publish` y el prompt A no es utilizable (el integrador no tendría el detalle). Alternativa no implementada, registrada en `alcance.md`: entregar el detalle completo en el prompt.
- **Ramas `audit/*`:** una por ronda; se eliminan al cerrar el ciclo. Si el ciclo se abandona sin `APROBADO`, quedan hasta que se cierre otro ciclo o se borren a mano.
- **No hay registros tras el cierre.** Este repositorio no guarda informes: el informe de cada ronda vive en la rama `audit/*` del repositorio auditado mientras dura el ciclo, y el informe final solo en la conversación. Al cerrar, `purge` elimina los archivos de trabajo. La trazabilidad que perdura es la del repositorio auditado (los commits de corrección y el merge del integrador).
- **Permiso de borrado:** eliminar ramas remotas exige escritura; si el remoto lo rechaza, `cleanup` falla y se informa sin reintentar por otra vía.
- **Repositorios privados en la nube:** requieren adjuntar el repositorio a la sesión con acceso de escritura.
- **Archivos renombrados** durante la corrección cambian la huella y aparecen como resuelto más nuevo.
- **Confianza en el integrador:** el cierre es un dato, no una orden; sus textos se tratan como no confiables.
