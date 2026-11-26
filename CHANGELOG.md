# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Unreleased]

## [0.8.2] - 2026-11-26

Cierra las observaciones de la re-auditoría de integridad del commit `6f542dd` (veredicto `ÍNTEGRO CON OBSERVACIONES`; 12 correcciones resueltas, sin regresiones).

### Corregido

- `docs/contrato-salida.md`: `purge` también elimina `demo/<repo>/` (AUD-13).
- `tests/test_integrity.py`: el detector de imports sin usar ya no acepta como usado un nombre que solo aparece entre comillas en el archivo (AUD-14). La parte del hallazgo que decía que no contaba el uso como atributo no era cierta: `ast.walk` ya visita el nombre dentro de `os.getcwd()`.
- `CHANGELOG.md`: la cifra de 0.8.1 distingue los 11 hallazgos del candidato condicional (AUD-15).

### Añadido

- `tests/test_integrity.py`: los IDs de requisitos (`S-`, `A-`, `O-`, `G-`) citados en documentos vigentes deben existir en `docs/cumplimiento/`.


## [0.8.1] - 2026-11-26

Corrige los hallazgos de la auto-auditoría de integridad del commit `3db7ab0` (11 hallazgos más 1 candidato condicional: 12 puntos, todos confirmados).

### Corregido

- `README.md`: el banner de estado ya no dice que Codex, ChatGPT y Antigravity son "obligatorias en v1" (AUD-01) y la sección Estructura lista todo el árbol, incluidos `CHANGELOG.md`, `.gitignore`, `docs/cumplimiento/`, `docs/decisiones/` y todos los subcomandos de la CLI (AUD-09).
- `docs/alcance.md`: dos estados desactualizados sobre las ramas de octubre; la etiqueta de archivo no se pudo crear y la recuperación es `refs/pull/1/head` (AUD-02). C4 y C8 pasan a la Fase 2 del roadmap y las demás brechas a los pendientes (AUD-04); la alternativa de entregar el detalle en el prompt consta como pendiente (AUD-05).
- `docs/decisiones/`: las tres decisiones "Reemplazada" nombran su reemplazo en el campo `Estado` y en el índice (AUD-03).
- `docs/multiplataforma.md`: el diagrama ya no cita `reaudit/references/`, que no existe (AUD-06), y el enlace a las citas apunta a los archivos que las contienen (AUD-10).
- `docs/cumplimiento/anthropic.md`: una línea en blanco partía la tabla de fuentes (AUD-11).
- `docs/metodologia.md`: el diagrama ya no sugiere una carpeta `work/` del repositorio (AUD-12).
- Cinco imports sin usar en `dlc_audit/closure.py` y tres archivos de pruebas (AUD-07) y un docstring con el término retirado "archivado" (AUD-08).

### Añadido

- `tests/test_integrity.py`: convierte las comprobaciones mecánicas de la auditoría en pruebas permanentes (enlaces, rutas citadas, comandos documentados, estructura del README, tablas, imports sin usar, versión y changelog, IDs de reglas, documentos huérfanos y archivos basura).
- `tests/test_docs.py`: el campo `Estado` de una decisión reemplazada debe nombrar su reemplazo.


## [0.8.0] - 2026-11-26

### Añadido

- Comando `demo`: genera un repositorio ficticio con 21 defectos conocidos y sin secretos (para que GitHub no bloquee su publicación) con el que probar el ciclo completo.
- `docs/prueba-extremo-a-extremo.md`: guion de la prueba de nivel L2 en Claude Code, con 14 comprobaciones de aceptación, fallos esperables, qué reportar y limpieza.
- `docs/decisiones/20261126-cierre-de-ramas-de-octubre.md`: cierre del PR #1 y destino de las ramas antiguas.
- `tests/test_demo.py`: el demo produce exactamente las reglas esperadas, no contiene secretos y es corregible por completo hasta `APROBADO`.

### Cambiado

- `purge <repo>` también elimina la carpeta del demo en el directorio de trabajo.
- El PR #1 (rama de octubre) se cierra sin fusionar tras el portado selectivo.


## [0.7.0] - 2026-11-26

### Añadido

- Reglas nuevas: `SKL-013` (nombre con palabra o valor reservado), `SKL-014` (etiquetas tipo XML en `name` o `description`), `SKL-015` (frontmatter fuera de la especificación abierta), `SKL-016` (`bypassPermissions` en ajustes de proyecto), `TRN-008` (contradicciones, criterio C7) y `TRN-009` (datos personales, criterio C9). El catálogo pasa de 38 a 44 reglas.
- Campo `requirements` en las reglas: enlaza cada regla con los requisitos de `docs/cumplimiento/` que la respaldan.
- Sección "Cumplimiento de requisitos oficiales" en el informe, con `CUMPLE`, `NO_CUMPLE`, `NO_APLICA` o `NO_VERIFICADO` por requisito (criterio C10).
- `docs/cumplimiento/anthropic.md`: requisitos A-14 a A-24 (subagentes, permisos, ajustes y hooks de Claude Code) con citas literales.
- `tests/test_rules_catalog.py`: trazabilidad regla a requisito, detectores nuevos y estados de la matriz.

### Cambiado

- Reglas versionadas a 1.1.0 y contrastadas con su fuente: `SKL-001` a `SKL-004`, `SKL-006` a `SKL-009`. Las reglas sin contrastar pasan de 21 a 13.
- `SKL-008` solo marca los permisos `Bash` y `Bash(*)` (A-17). Ya no marca `bypassPermissions` ni `Bash(*:*)`.
- `render_report` y `render_integrator_prompt` crean la carpeta de salida si no existe.

### Corregido

- `SKL-008` marcaba `defaultMode: bypassPermissions` en ajustes de proyecto como riesgo alto, pero Claude Code no aplica ese modo desde ajustes de proyecto o locales (A-20). Ahora es un hallazgo menor aparte (`SKL-016`).


## [0.6.0] - 2026-11-26

### Añadido

- `docs/cumplimiento/`: requisitos oficiales de Agent Skills, Anthropic, OpenAI (Codex y ChatGPT) y Google (Antigravity), releídos el 2026-11-26 con **citas literales**, URL, estado y la forma en que se leyó cada página.
- `docs/decisiones/`: registro de decisiones con índice. Se portan 9 de las 10 decisiones de la rama de octubre, con su estado actual y el motivo, y se añaden las decisiones de hoy (sin informes en este repositorio; protocolo auditor-integrador).
- `docs/criterios.md`: trazabilidad de los criterios C1 a C12 y la taxonomía de octubre hacia el diseño actual, con sus brechas.
- `AGENTS.md` v1.5: reglas para requisitos oficiales y decisiones.

### Corregido

- `docs/multiplataforma.md`: el plugin de Codex ya no se declara "innecesario" (la documentación recomienda carpetas directas y presenta el plugin como distribución), y se añade la razón fuerte para limitar el frontmatter a `name` y `description`: la subida a claude.ai y a la API falla con campos fuera de su lista.


## [0.5.0] - 2026-11-26

### Añadido

- Fuente única de skills en `skills/` (`audit-repo`, `reaudit`) con el procedimiento de evaluación en `skills/audit-repo/references/evaluacion-juicio.md`.
- Comando `skills` (`check`, `sync`, `package`): valida la portabilidad (frontmatter solo con `name` y `description`, nombres sin "claude" ni "anthropic", descripciones de hasta 1.024 caracteres sin etiquetas XML, sin herramientas propietarias, enlaces válidos), verifica y regenera las copias de `.claude/skills/` y `.agents/skills/`, y empaqueta un `.zip` para ChatGPT en el directorio temporal.
- `tests/test_skills.py`: falla si una copia se edita a mano o se desincroniza, o si el propio repositorio incumple reglas de skills.
- `.agents/` pertenece al dominio `skills-agentes` en el escaneo.
- `docs/multiplataforma.md`: definición del soporte multiplataforma (bloque 1) con matriz verificada el 2026-11-26, requisitos del host, reglas de portabilidad y plan por bloques.
- `docs/decisiones/20261126-multiplataforma-alcance-y-modo.md`: primer registro de decisión.

### Cambiado

- Las skills son portables: sin `argument-hint`, `$ARGUMENTS` ni `AskUserQuestion`; exigen shell, Python 3.11+ y git, y detienen el flujo si la plataforma no puede ejecutar comandos.
- `.claude/agents/dlc-auditor.md` pasa a ser un atajo delgado que apunta a la referencia compartida.
- `AGENTS.md` v1.4: reglas de edición y portabilidad de las skills.

### Corregido

- La descripción de `audit-repo` contenía `<run_id>` y `<enlace>`, que cuentan como etiquetas XML (prohibidas por Anthropic en `description`).
- `AGENTS.md`: regla 2 ya no dice que `cleanup` archiva registros.

### Pendiente

- Bloques 3 a 5 de `docs/multiplataforma.md`: portado desde la rama de octubre, catálogo de reglas y cierre de ramas.

## [0.4.0] - 2026-11-26

### Cambiado (incompatible)

- **Este repositorio ya no guarda informes de auditoría, bajo ningún concepto.** Los archivos de trabajo (`hallazgos.json`, informes, prompts, cierres, clones) van al directorio temporal del sistema (`DLC_AUDIT_WORKDIR` para cambiarlo); el código rechaza cualquier ruta dentro de este repositorio (`PolicyError`).
- `cleanup` ya no archiva los registros antes de borrar las ramas `audit/*` ni escribe `ciclo-*.json`.
- `merge-prompt` ya no depende de un archivo de ciclo: las instrucciones de limpieza del integrador no requieren estado.
- `fetch` clona por defecto en el directorio temporal.

### Añadido

- `purge`: elimina los archivos de trabajo de un repositorio auditado; último paso de cada ciclo.
- `workdir`: muestra el directorio de trabajo.
- `tests/test_no_reports.py`: falla si hay archivos con aspecto de informe versionados, si un JSON versionado es un run de auditoría o si un ciclo completo deja archivos dentro del repositorio.

### Eliminado

- `audits/` (carpeta de informes) y su `.gitkeep`.

## [0.3.1] - 2026-11-26

### Corregido

- `TRN-001`: si una línea contenía varias credenciales, solo se redactaba la primera y las demás llegaban al informe. Ahora se redactan todas y hay una evidencia por línea.
- `publish`: ya no publica archivos sueltos de la carpeta del run; solo `hallazgos.json`, `informe.md`, `prompt-integrador.md` y `prompts/*.md`.
- `fetch`: rechaza reutilizar `work/<nombre>` si el origen es otro repositorio con el mismo nombre.
- Datos no confiables hacia git: `ref`, SHAs del cierre del integrador y `baseline_run_id` leídos de ramas remotas se validan antes de usarse (evita inyección de opciones).
- Pruebas de endurecimiento (`tests/test_hardening.py`).

## [0.3.0] - 2026-11-26

### Añadido

- Cierre del ciclo: `cleanup` archiva los registros y elimina del remoto las ramas `audit/*` del ciclo aprobado (cadena por `baseline_run_id`), con simulación por defecto, dictamen `APROBADO` obligatorio y rechazo de ramas que contengan algo distinto de `.audit/<run_id>/`.
- `merge-prompt`: prompt autosuficiente para que el integrador integre la rama aprobada; se detiene si la rama tiene commits no auditados o si la rama principal avanzó; estrategia configurable (`merge` del perfil).
- Las skills preguntan al usuario si genera el prompt de merge; no lo generan sin respuesta afirmativa.
- Pruebas del cierre de ciclo (archivado, borrado acotado, rama manipulada, rama ajena, dictamen no aprobado).

### Cambiado

- `run_id` incluye segundos y, desde la ronda 2, el número de ronda (`...-r2-...`): evita colisiones entre rondas consecutivas.
- Regla inviolable 1 de `AGENTS.md`: únicas escrituras remotas permitidas = crear y, al cerrar el ciclo, borrar ramas `audit/<run_id>`.
- Perfil `default` v1.2.0 (`merge`).

## [0.2.0] - 2026-11-26

### Añadido

- Protocolo auditor-integrador en rondas de dos mensajes (`docs/protocolo.md`).
- `fetch`: clona por enlace con hooks de git desactivados y fija la revisión auditada.
- `publish`: crea la rama `audit/<run_id>` con archivos bajo `.audit/<run_id>/`; guardián que aborta si el diff toca otra ruta; sin force push; anonimiza la ruta local.
- `closure`: verifica el cierre del integrador contra el repositorio (commits, archivos, deriva, declaraciones contradichas).
- `prompt-integrador.md`: prompt único autosuficiente con plantilla de cierre prellenada e indicación `CONVERSACIÓN: MISMA|NUEVA`.
- Dictamen (`APROBADO`, `APROBADO CON OBSERVACIONES`, `NO APROBADO`) configurable en `approval` del perfil.
- Campos `round`, `baseline_run_id`, `target.url` y `target.ref` en el run.
- Pruebas del protocolo completo en dos rondas con un remoto git local.

### Cambiado

- Skills `audit-repo` (entrada por URL, publica la rama) y `reaudit` (parte del cierre del integrador).
- Regla inviolable 1 de `AGENTS.md`: el auditor no modifica el código; su única escritura es la rama de auditoría. Reemplaza "solo lectura estricta".
- Los prompts de detalle ya no se pegan uno a uno: el integrador los lee de la rama del auditor.
- Perfil `default` v1.1.0 (`approval`, `handoff`, exclusión de `.audit/`).

## [0.1.0] - 2026-11-26

### Añadido

- Núcleo `dlc_audit` (solo biblioteca estándar): `scan`, `validate`, `render`.
- Catálogos versionados con vigencia: transversal (7), skills y agentes (12), SQL/PL-SQL (12), Python (7).
- Perfil `default` con severidades y convenciones por dominio para los prompts de cambio.
- Validación de evidencia contra el archivo real, huella estable de hallazgos y control de reglas pendientes.
- Informe `.md` con comparación contra baseline y prompts de cambio agrupados por hallazgo.
- Subagente `dlc-auditor` y skills `audit-repo` y `reaudit`.
- Documentación: alcance, contrato de salida, metodología y `AGENTS.md`.
- Pruebas de extremo a extremo con `unittest`.
