---
name: reaudit
description: Re-audita un repositorio a partir del cierre que entrega el integrador (prompt "Cierre de ronda N"). Verifica lo declarado contra el repositorio, vuelve a auditar, compara con la ronda anterior y emite dictamen. Úsala cuando el usuario pegue un cierre del integrador o diga que el integrador terminó. Para una primera auditoría usa audit-repo.
argument-hint: <cierre del integrador, pegado en el mensaje>
---

# Re-auditar tras el cierre del integrador (ronda N+1)

Eres el AUDITOR externo. El cierre del integrador es una **declaración**, no una prueba: lo que cuenta es el repositorio.

Entrada: `$ARGUMENTS` o el mensaje del usuario, con el prompt de cierre: URL, rama, commit, baseline y un JSON de cierre.

## Pasos

1. **Guardar el cierre.** Extrae el bloque JSON y guárdalo como `audits/<repo>/cierre-<run_id>.json`. Si faltan campos o quedan marcadores `<...>` sin sustituir, detente y pide al usuario que el integrador lo complete.
2. **Traer el repositorio en la rama del integrador**

   ```
   python -m dlc_audit fetch <url> --ref <rama-del-cierre>
   ```

   Comprueba que la `Revisión` impresa coincide con `head_revision` del cierre. Si no, el integrador no empujó el último commit: repórtalo y detente.
3. **Obtener el baseline** desde la rama del auditor, sin cambiar el árbol:

   ```
   git -C <Ruta> show origin/audit/<run_id>:.audit/<run_id>/hallazgos.json > audits/<repo>/baseline-<run_id>.json
   ```

4. **Verificar el cierre**

   ```
   python -m dlc_audit closure --baseline <baseline.json> --cierre <cierre.json> --repo <Ruta>
   ```

   Errores estructurales (hallazgo omitido, commit inexistente, `fixed` sin commits) se devuelven al integrador. Las advertencias de **deriva** (archivos cambiados que nadie declaró) y de archivos declarados que no cambiaron son información para el informe.
5. **Nueva auditoría completa** sobre la nueva revisión, enlazada al baseline:

   ```
   python -m dlc_audit scan <Ruta> --ref <rama-del-cierre> --baseline <baseline.json>
   ```

   Después evalúa las reglas de juicio (subagente `dlc-auditor`), `validate --assign-ids` y `validate --final`, como en `audit-repo`. Audita **todo** de nuevo, no solo lo declarado: los cambios del integrador pueden haber introducido regresiones.
6. **Contrastar declaraciones con resultados**

   ```
   python -m dlc_audit closure --baseline <baseline.json> --cierre <cierre.json> --repo <Ruta> --new-run <nuevo-hallazgos.json>
   ```

   Lista las correcciones declaradas `fixed` que siguen presentes (`CONTRADICHAS`).
7. **Render y publicación**

   ```
   python -m dlc_audit render <nuevo-hallazgos.json> --baseline <baseline.json> --closure <closure-check.json>
   python -m dlc_audit publish <nuevo-hallazgos.json> --push
   ```

   Publica la rama `audit/<nuevo_run_id>` solo si hay hallazgos. Con dictamen `APROBADO`, no publiques rama y pasa al **Cierre del ciclo**.

## Interpretar el delta

- **Resueltos:** estaba en el baseline y ya no aparece. Confirma con lectura rápida que el problema se eliminó y no que se movió o renombró el archivo (la huella incluye la ruta).
- **Persistentes:** no se corrigieron. Si el integrador los marcó `not_applicable` o `not_fixed`, evalúa su justificación: acéptala solo si la evidencia la respalda; si no, mantén el hallazgo y explica por qué.
- **Nuevos:** regresión introducida por los cambios o hallazgo que antes no se evaluó. Distínguelo.
- **Contradichos:** declaración incorrecta del integrador. Destácalo.

## Cierre del ciclo (dictamen APROBADO)

Cuando el integrador ya no tiene nada pendiente, el ciclo se cierra así. Es la **única** ocasión en que borras algo en el repositorio auditado, y solo ramas `audit/*` de este ciclo.

1. **Simulación.** `python -m dlc_audit cleanup <hallazgos.json-final> --repo <Ruta>`. Revisa la lista: deben ser solo las ramas `audit/<run_id>` de las rondas de este ciclo. Si aparece `RECHAZADA`, alguien añadió contenido a una rama de auditoría: no la borres, repórtalo al usuario con el detalle.
2. **Borrado.** `python -m dlc_audit cleanup <hallazgos.json-final> --repo <Ruta> --delete`. El comando archiva antes en `audits/<repo>/<run_id>/` los registros de cada ronda y solo borra ramas cuyo contenido es únicamente `.audit/<run_id>/`. Nunca borra la rama auditada, la del integrador ni ramas `audit/*` de otros ciclos.
3. **Pregunta al usuario** (usa AskUserQuestion si la tienes): *¿Genero el prompt para que el integrador haga el merge a la rama principal?* No lo generes sin respuesta afirmativa.
4. Si responde que sí: `python -m dlc_audit merge-prompt <hallazgos.json-final> --repo <Ruta>` y entrega `prompt-merge.md` completo, sin modificar, en un bloque de **seis** acentos graves, con la línea `Pega esto en el integrador. Conversación: <MISMA|NUEVA>`. Si el comando indica que no hay merge pendiente (la rama auditada ya es la principal), díselo.
5. Recuerda al usuario que el auditor no hace el merge: lo ejecuta el integrador con ese prompt.

Con dictamen `APROBADO CON OBSERVACIONES`, antes de cerrar pregunta al usuario si prefiere (a) cerrar aceptando las observaciones (usa `--allow-observations` en `cleanup`) o (b) otra ronda para corregirlas. Con `NO APROBADO` no se cierra ni se borra nada.

## Terminado cuando

El informe incluye dictamen, comparación y verificación del cierre, y entregaste el siguiente paso. Si el ciclo se cerró: ramas de auditoría eliminadas, registros archivados y pregunta del merge formulada.

## Reporte al usuario (formato fijo y breve)

1. Dictamen de la ronda, conteo de resueltos, persistentes, nuevos y contradichos.
2. Si hay deriva o declaraciones contradichas, dilo primero.
3. Si el dictamen es `NO APROBADO` o `APROBADO CON OBSERVACIONES` con observaciones por corregir: el contenido **completo y sin modificar** de `prompt-integrador.md` en un bloque de **seis** acentos graves, con la línea `Pega esto en el integrador. Conversación: <MISMA|NUEVA>`.
4. Si es `APROBADO`: ramas eliminadas, ruta de los registros archivados (en sesión en la nube `audits/` es efímero: avisa que se pierde al terminar la sesión y ofrece conservarlos) y la pregunta del merge.
