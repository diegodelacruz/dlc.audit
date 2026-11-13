# Prompt de corrección: PR #32 (`claude/segundo-plano-reordenar-items`)

Origen: `auditorias/apex.skills/2026-11-13-auditoria-pr32-segundo-plano.md`, hallazgos R-01 a R-04, con las decisiones de la persona usuaria del 2026-11-13.

---

```text
Trabaja sobre la rama `claude/segundo-plano-reordenar-items` (PR #32) de `apex.skills`. No crees otra rama ni otro PR: agrega commits a este.

Contexto: una auditoría externa (`dlc.audit`, 2026-11-13) revisó el commit `606f814` y reportó los hallazgos R-01 a R-04. Ya decidí cómo se trata cada uno. Tu trabajo es corregir lo que indico y documentar la justificación de lo que se acepta por diseño. No reabras esas decisiones. Si encuentras evidencia técnica que las contradiga, detente y repórtala antes de cambiar nada.

Antes de empezar, lee `docs/POLITICA-EVOLUCION-ECOSISTEMA.md`, `skills/apex/references/modo-ejecucion.md`, `skills/apex-page-automation-safe/references/reordenar-elementos-pagina.md`, `scripts/apex_controlled_mcp.py` y `docs/decisiones/20261113-segundo-plano-y-reordenar-elementos.md`.

## R-01: copia entre ambientes (por diseño; hay que hacerla explícita)

Decisión: las skills SÍ pueden copiar entre ambientes, en cualquier sentido (TEST→PROD, PROD→TEST, etc.). El único límite son los privilegios de la cuenta autenticada en cada ambiente. No agregues bloqueos ni confirmaciones adicionales por ese motivo.

Lo que sí hay que corregir: hoy la receta fija el export en `-Environment test` (paso 3) y llama a `deploy_apex_page` sin `environment` (paso 4). Eso hace que el destino dependa de `DB_ENV` en `.env` y no de lo que la persona eligió. La copia entre ambientes debe ser una decisión explícita, no un efecto implícito.

1. En la receta, separa **ambiente de origen** (export) y **ambiente de destino** (import). Ambos se resuelven en la pregunta única; si la persona da uno solo, origen = destino.
2. El paso 3 usa el ambiente de origen resuelto (sin `test` fijo). El paso 4 pasa siempre `environment=<destino>` a `deploy_apex_page`.
3. Cuando origen ≠ destino, la propuesta de la pregunta única lo muestra en una línea ("Copia <origen> → <destino>"), sin pedir una confirmación adicional.
4. Verifica y documenta qué necesita un export de página de un ambiente para importarse en otro: workspace, application id, offset, `apex_application_install`. Comprueba si `deploy_apex_page` lo cubre hoy. Si falta algo, documéntalo como limitación conocida; no lo inventes. Marca lo no verificado en vivo como no verificado.
5. Documenta en `CLAUDE.md`, en `skills/apex/SKILL.md` (Environment Policy) y en la receta que la copia entre ambientes está permitida y que solo la limitan los privilegios de la cuenta. La regla actual "Never silently switch environments" sigue vigente: copiar entre ambientes elegidos explícitamente no es un cambio silencioso.
6. Agrega pruebas que fallen si la receta vuelve a contener un ambiente fijo o si `deploy_apex_page` aparece sin `environment`.

## R-02: control de contenido del import (aceptado por diseño; solo documentar)

Decisión: el control del contenido importado queda a discreción de la persona usuaria, y las skills preguntan si se hace backup. No agregues validadores de diff ni chequeos de concurrencia.

Documenta en el registro de decisión (sección de riesgos aceptados) y en la receta, en pocas líneas y sin alarmismo:
- el import reemplaza la página completa con el contenido del archivo;
- la revisión de que el diff se limite a `p_item_sequence`/`p_begin_on_new_line` la hace el agente y queda a criterio de la persona;
- un cambio hecho por otra persona en la página entre el export y el import se sobrescribe;
- el backup, si la persona lo pide, es la vía de recuperación.

## R-03: export por la ruta PowerShell heredada (corregir)

Decisión: se resuelve. Implementa en `scripts/apex_controlled_mcp.py` una herramienta MCP de solo lectura `export_apex_page`:
- parámetros: `application_id: int`, `page_id: int`, `environment: str` (explícito, sin caer en `DB_ENV` cuando falta: si no viene, devuelve `ENVIRONMENT_REQUIRED`);
- ejecuta `apex export-components -applicationid <app> -expcomponents "PAGE:<page>" -skipexportdate -overwrite-files` con el runtime SQLcl administrado y la conexión por stdin, igual que `sqlcl_result`;
- escribe solo dentro de `.codex-tmp/apex-pages/f<app>_p<page>/`; valida enteros y ruta con el mismo criterio que `workspace_sql_file`;
- verifica que el archivo generado contenga `wwv_flow_imp.import_begin` e `import_end`;
- devuelve la ruta relativa, el sha256 y el ambiente; registra un evento de lectura en la bitácora, sin SQL ni credenciales;
- anotaciones: `readOnlyHint: true`; `destructiveHint: false`.

Después:
1. Reemplaza el bloque PowerShell del paso 3 de la receta por `export_apex_page`. La receta ya no debe depender de `Initialize-OracleConnection.ps1` ni de `$env:APEX_SQLCL_CONN`.
2. Agrega pruebas unitarias con SQLcl simulado: ambiente obligatorio, ids no enteros rechazados, ruta fuera de `.codex-tmp` imposible, archivo sin `import_begin`/`import_end` rechazado, conexión nunca en argv, evento de bitácora sin secretos.
3. Actualiza la sección "Descontinuación" del registro de decisión: `export_apex_page` deja de ser una mejora posterior.

## R-04: automatización headless como segundo plano (por diseño; documentar lo que hace el repositorio)

Decisión: es el comportamiento previsto. La automatización headless (por ejemplo, Playwright sin ventana y sin la sesión del navegador de la persona) cuenta como segundo plano y puede usarse para leer **y** para cambiar componentes cuando corresponde. No la restrinjas.

Lo que falta es documentarlo con exactitud:
1. En `skills/apex/references/modo-ejecucion.md`, aclara que el modo segundo plano incluye automatización headless de App Builder con las credenciales de `.env`, que puede modificar componentes, y que aplica la misma pregunta única (ambiente, objeto, acción, backup, modo de pasos) que cualquier cambio.
2. Ajusta `CLAUDE.md` ("Background by default") y `AGENTS.md` para que no digan "never ... browser" de forma absoluta: lo que no se hace sin elegir control del equipo es usar el escritorio, ventanas visibles o la sesión del navegador de la persona.
3. Indica si los cambios headless quedan registrados en la bitácora. Si no quedan, dilo explícitamente como limitación, sin implementarlo en este PR.

## Cierre

- Alinea la pregunta única en todos los lugares donde se enumera: `CLAUDE.md` (Modifications), `docs/MANUAL-DE-USO.md`, `skills/apex/SKILL.md` (Fluency Policy), `step-mode.md` y `modo-ejecucion.md`. Debe incluir ambiente de origen/destino cuando aplique, objeto, acción, backup, paso a paso/todos los pasos y segundo plano/control del equipo.
- Actualiza `docs/decisiones/20261113-segundo-plano-y-reordenar-elementos.md`: agrega una sección "Revisión independiente (dlc.audit, 2026-11-13)" con una tabla R-01..R-04 → corregido / aceptado por diseño, la justificación y el archivo que lo resuelve. Mantén el estado "pendiente de revisión independiente" hasta la nueva auditoría.
- Actualiza `CHANGELOG.md` (Unreleased).
- Ejecuta `python scripts/run_ci_checks.py` y reporta el resultado real. Si algo falla, corrígelo; no omitas ni desactives pruebas.
- Respeta los estándares del repositorio: tabuladores en SQL, minúsculas, comas al inicio; guía genérica sin aplicaciones ni páginas concretas (usa marcadores y binds enteros).
- No te conectes a Producción. Si necesitas verificar algo en vivo, usa TEST, solo lectura, e indícalo.
- Haz commit en la misma rama, con push al PR #32, y entrega un resumen: hallazgo → acción → archivos → evidencia de prueba. Este PR volverá a pasar por la auditoría externa antes de fusionarse.
```
