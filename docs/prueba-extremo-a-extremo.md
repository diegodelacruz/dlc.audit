# Prueba de punta a punta en Claude Code (nivel L2)

Objetivo: demostrar que el ciclo completo (auditar, corregir, re-auditar, cerrar) funciona en Claude Code sobre un repositorio tuyo descartable. Es el requisito 3 del Definition of Done de v1 (`multiplataforma.md`). **Solo puedes ejecutarla tú**: hasta entonces el soporte de Claude Code consta como no probado de punta a punta.

El repositorio de demostración es **ficticio**: lo genera `python -m dlc_audit demo`, tiene 21 defectos conocidos y no contiene secretos, así que GitHub no bloqueará su publicación.

## Qué necesitas

- Una sesión de Claude Code (web o escritorio) abierta en un clon de `dlc.audit`, con Python 3.11 o superior y git.
- Una cuenta de GitHub que pueda crear un repositorio privado.
- Acceso de escritura de esa sesión al repositorio de demostración. En la nube, se concede adjuntándolo a la sesión con acceso `push`.

## Preparación: repositorio de demostración

1. En GitHub, crea un repositorio **privado y vacío** (sin README), por ejemplo `demo-auditoria`. Sirve la app móvil o github.com/new.
2. En una sesión sobre `dlc.audit` con acceso de escritura a ese repositorio, pide:

   > Ejecuta `python -m dlc_audit demo` y publica ese repositorio en `<usuario>/demo-auditoria`, rama `main`. No añadas nada más.

   En un equipo local: `python -m dlc_audit demo`, y dentro de la carpeta que imprime, `git remote add origin <url>` y `git push -u origin main`.
3. Comprueba en GitHub que `main` tiene **un commit y 6 archivos**.

## Ronda 1: el auditor

En una conversación nueva sobre `dlc.audit`, con acceso de escritura al repositorio de demostración:

```
/audit-repo https://github.com/<usuario>/demo-auditoria
```

## El integrador

Abre el repositorio de demostración con otro agente (o en otra conversación) y pega el **prompt A** que te entregó el auditor. Pídele que trabaje en una rama `correccion` en lugar de `main`: así se ejercita también el prompt de merge. Para llegar a `APROBADO` hay que corregir los 21 hallazgos; con solo los de severidad baja pendientes el dictamen sería `APROBADO CON OBSERVACIONES`.

Cuando termine, el integrador te responde con el **prompt B** (cierre).

## Ronda 2: re-auditoría y cierre del ciclo

Pega el cierre en la conversación del auditor, con `/reaudit`. Si el dictamen es `APROBADO`, el auditor simula el borrado de las ramas `audit/*`, lo ejecuta, te pregunta si genera el prompt de merge y, al final, purga sus archivos de trabajo.

## Comprobaciones de aceptación

| # | Momento | Qué debe ocurrir |
|---|---|---|
| 1 | Preparación | El demo en GitHub tiene un commit en `main` y 6 archivos |
| 2 | Ronda 1 | Dictamen `NO APROBADO` |
| 3 | Ronda 1 | El auditor detecta como mínimo las 21 reglas que imprime `python -m dlc_audit demo` (lista en `dlc_audit/demo.py`) |
| 4 | Ronda 1 | Existe una rama `audit/<run_id>` en el demo y contiene **solo** archivos bajo `.audit/<run_id>/` |
| 5 | Ronda 1 | `main` del demo no cambió (sigue en el mismo commit) |
| 6 | Ronda 1 | El prompt A llega completo, en un bloque de seis acentos graves, con `CONVERSACIÓN: MISMA` o `NUEVA` |
| 7 | Ronda 1 | El informe incluye la sección "Cumplimiento de requisitos oficiales" |
| 8 | Ronda 1 | `git status` de `dlc.audit` no muestra archivos nuevos |
| 9 | Ronda 2 | El auditor verifica el cierre contra el repositorio y comprueba commits y archivos declarados |
| 10 | Ronda 2 | Dictamen `APROBADO` (o `APROBADO CON OBSERVACIONES` si quedaron observaciones bajas) |
| 11 | Cierre | `cleanup` en simulación lista solo las ramas `audit/*` de este ciclo |
| 12 | Cierre | Se pregunta si se genera el prompt de merge, y no se genera sin tu respuesta afirmativa |
| 13 | Cierre | Con la rama `correccion`, el prompt de merge indica `main` como destino y exige comprobar el commit aprobado |
| 14 | Cierre | Al terminar, `git status` de `dlc.audit` sigue limpio y `python -m dlc_audit workdir` no contiene tu repositorio de demostración |

## Fallos esperables

- **403 al borrar ramas:** puede ocurrir en una sesión en la nube; `cleanup --delete` falla y lo informa sin reintentar por otra vía. Anota que ocurrió y borra las ramas `audit/*` a mano. Cuenta como comportamiento correcto, no como fallo del flujo.
- **Plataforma sin shell:** las skills se detienen y lo dicen en vez de simular resultados.
- **Las skills no aparecen:** comprueba que la sesión se abrió en el clon de `dlc.audit` y ejecuta `python -m dlc_audit skills check`.
- **El auditor no puede publicar la rama:** falta acceso de escritura al repositorio de demostración; el flujo debe llegar hasta `render` y avisarlo.

## Qué reportar

Responde en la conversación con cada comprobación como `PASA` o `FALLA`, y para cada `FALLA` el mensaje de error o lo que viste. No hace falta pegar informes: el demo es ficticio y los informes no se guardan.

## Limpieza

1. Borra el repositorio de demostración en GitHub (*Settings*, zona de peligro).
2. Ejecuta `python -m dlc_audit purge demo-auditoria` para eliminar sus archivos de trabajo, incluido el demo generado.
3. Borra a mano las ramas que el servidor haya impedido borrar.
