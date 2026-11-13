# Auditoría del cambio no fusionado: PR #32 "Segundo plano por defecto y receta para reordenar ítems APEX"

| Campo | Valor |
|---|---|
| Fecha | 2026-11-13 |
| Repositorio | `diegodelacruz/apex.skills` |
| Rama | `claude/segundo-plano-reordenar-items` |
| Commit | `606f814` (base `e096cd1` = `main`) |
| PR | #32, abierto, sin fusionar |
| CI del PR | Run 127: `success` (GitHub Actions, `pull_request`) |
| Decisión auditada | `docs/decisiones/20261113-segundo-plano-y-reordenar-elementos.md` (estado: "pendiente de revisión independiente") |
| Método | Revisión estática del diff; verificación textual de las aserciones de la prueba nueva; comprobación de la resolución de ambiente en el código del MCP |
| Informe previo | `2026-11-13-auditoria-integral.md` (sobre `main`) |

## Ramas revisadas

| Rama | Último commit | Cambio frente a `main` | En alcance |
|---|---|---|---|
| `claude/segundo-plano-reordenar-items` | 2026-11-13 | 1 commit, 14 archivos, +356/−11 | **Sí (cambio de hoy)** |
| `dependabot/pip/fastmcp-gte-4.1.4-and-lt-5.0.0` | 2026-11-01 | `requirements.txt` (fastmcp 3→4, versión mayor) | No; ver nota final |
| `dependabot/pip/black-26.10.1`, `isort-gte-9.0.2`, `pillow-gte-13.0.0` | 2026-11-01 | 1 línea cada una | No |

`main` no cambió desde la auditoría integral (`e096cd1`).

## Limitaciones

- No ejecuté código del repositorio. Las pruebas pasan según la CI del PR (run 127). Además, comprobé estáticamente que cada cadena que afirma `tests/test_execution_mode.py` existe en los archivos.
- No hubo conexión a Oracle/APEX. Las afirmaciones sobre la semántica del export APEX se marcan **[Inferencial]**.
- La nueva visibilidad privada del repositorio no se verificó directamente: esta sesión ahora accede con credenciales.

## Resumen

El cambio es de bajo riesgo en su primera mitad: el modo segundo plano unifica la regla del navegador entre `AGENTS.md`, `CLAUDE.md` y el coordinador, y **corrige la contradicción M-05** del informe previo. La segunda mitad, la receta para reordenar ítems, **introduce una ruta de escritura en vivo con un defecto bloqueante**: puede exportar de TEST e importar en otro ambiente.

**Dictamen: solicitar cambios antes de fusionar** (por R-01; R-02 y R-03 son recomendables en la misma iteración).

| Severidad | Cantidad |
|---|---|
| Alta | 1 |
| Media | 3 |
| Baja | 5 |

---

## Hallazgos

### R-01 (Alta, bloqueante). La receta puede exportar de TEST e importar en otro ambiente

**Evidencia**

- `reordenar-elementos-pagina.md:56`: el paso 3 fija `Initialize-OracleConnection.ps1 -Environment test`.
- `reordenar-elementos-pagina.md:80`: el paso 4 llama a `deploy_apex_page` sin el parámetro `environment`.
- `scripts/apex_controlled_mcp.py:175`: `selected = environment or values.get("DB_ENV")`. Sin `environment`, el import va al ambiente que indique `DB_ENV` en `.env`.

**Escenario de falla:** la persona aprueba el cambio en Producción, o `DB_ENV=production` en `.env`. El agente exporta la página **de TEST**, la edita e importa ese export completo en **Producción**. Así reemplaza la página productiva con la versión de TEST, no solo el orden de los ítems. El paso 5 (validación de orden y `condition_type_code`) no detectaría diferencias en fuentes, procesos o validaciones.

Además, la pregunta única pide el ambiente, pero la receta no lo usa en ninguno de los dos pasos.

**Recomendación**

1. Parametrizar el paso 3 con el ambiente resuelto en la pregunta única (`-Environment <ambiente>`).
2. Exigir `environment=<ambiente>` en el paso 4.
3. Antes de importar, verificar que el export y el destino sean el mismo ambiente. Por ejemplo, registrar en el paso 3 el `db_unique_name` o servicio y compararlo con el de la sesión de import.
4. Agregar una prueba que falle si la receta contiene un ambiente fijo o si `deploy_apex_page` aparece sin `environment`.

### R-02 (Media). El import reemplaza la página completa y nada impone que el diff se limite a dos parámetros

**Evidencia**

- Paso 4: "el diff debe contener solo esas líneas". Lo verifica el agente, no una herramienta.
- `deploy_apex_page` solo comprueba `import_begin`/`import_end`; el export editado vive en `.codex-tmp/` (ignorado por Git) y nadie lo revisa.
- El paso 5 valida orden, filas y `condition_type_code`, no el resto de atributos.

**Riesgos**

- Una edición errónea (otro ítem, otro parámetro) se importa sin control. Es el mismo error documentado en la decisión ("un ítem renumerado por error").
- **[Inferencial]** Si alguien modifica la página en App Builder entre el export y el import, esos cambios se pierden sin aviso (agrava M-03 y M-04 del informe previo).

**Recomendación**

1. Agregar un validador determinístico, por ejemplo `scripts/validate_item_layout_diff.py <original> <editado>`. Debe fallar si el diff toca algo distinto de `p_item_sequence`/`p_begin_on_new_line` o ítems fuera de la lista aprobada.
2. Inmediatamente antes del import, volver a leer `last_updated_on` de la página y abortar si cambió desde el export.
3. En el paso 5, comparar también una huella de los atributos no relacionados con la distribución, antes y después.

### R-03 (Media). La receta usa la ruta PowerShell heredada, con la contraseña en una variable de entorno

**Evidencia:** el paso 3 ejecuta `Initialize-OracleConnection.ps1`, que deja `user/password@host:port/service` en `$env:APEX_SQLCL_CONN` durante el resto de la sesión PowerShell. Ese proceso lo heredan todos sus procesos hijos (hallazgo M-09 previo). Es la primera receta operativa que **promueve** esa ruta en lugar del MCP controlado.

Otros efectos:

- El export queda fuera de la bitácora.
- **[Inferencial]** El export usa el SQLcl del perfil de usuario y el import usa el runtime administrado: pueden ser versiones distintas.
- La receta solo funciona en Windows/PowerShell.

**Recomendación:** implementar ya la herramienta MCP `export_apex_page`, de solo lectura, con el ambiente explícito, la ruta limitada a `.codex-tmp/` y registro en la bitácora. La decisión la dejó como mejora posterior, pero es lo que cierra R-01 y R-03 a la vez. Mientras tanto, limpiar `$env:APEX_SQLCL_CONN` en un bloque `finally`.

### R-04 (Media). "Headless" se considera segundo plano: automatizar App Builder sin preguntar queda permitido

**Evidencia:** según la tabla de `modo-ejecucion.md`, el segundo plano incluye "automatización *headless* que no muestra ventanas ni usa la sesión del navegador de la persona". La decisión agrega: "Playwright headless cuenta como segundo plano". `CLAUDE.md` dice "Never take control of the user's computer (browser, …)".

**Riesgo:** un agente puede iniciar sesión en App Builder con las credenciales de `.env` y modificar componentes por la UI, sin la elección de control del equipo y fuera de la bitácora del MCP. La regla protege el escritorio, pero no la superficie de cambios.

**Recomendación:** limitar el headless a **lecturas**, como capturas o verificación visual, o exigir para cambios por UI la misma elección explícita.

### R-05 (Baja). La pregunta única no quedó alineada en todos los lugares

`step-mode.md` y `modo-ejecucion.md` agregan el campo de ejecución. No lo incluyen:

- `CLAUDE.md`, sección *Modifications*: sigue listando 5 campos;
- `docs/MANUAL-DE-USO.md`: "ambiente, objeto, acción y backup sí/no", sin pasos ni ejecución;
- `skills/apex/SKILL.md`, viñeta de confirmación de *Fluency Policy*.

Contradice la consistencia de la política (§3).

### R-06 (Baja). La semántica de la cuadrícula es incompleta

**[Inferencial]** La receta solo considera `p_begin_on_new_line`. La vista expone `new_grid_row`, `new_grid_column` y `grid_column`, y la propia evidencia los menciona. Un ítem con columna fija o con `begins_on_new_cell` no estándar puede romper las parejas aunque la secuencia sea correcta.

**Recomendación:** en el paso 2, si `grid_column` no es nulo o `begins_on_new_cell`/`new_grid_column` difieren del valor por defecto, informarlo y excluir el ítem o pedir la decisión.

### R-07 (Baja). El backup queda en una carpeta temporal ignorada

En el paso 3, la copia de backup se guarda en `.codex-tmp/`, ignorado por Git y sin retención. Mejora respecto de M-04, porque ahora el export es reciente. Pero el rollback depende de que nadie limpie esa carpeta.

**Recomendación:** mover el backup a `control-proyecto/backups/<fecha>_<app>_<página>/` (ignorado y con retención documentada); la bitácora ya registra su `sha256`.

### R-08 (Baja). Las pruebas son de redacción, no de comportamiento

`tests/test_execution_mode.py` comprueba que existan frases. Por ejemplo, `"or the browser as\n  available and applicable" not in skill` pasa ante cualquier redacción nueva. No protegen contra R-01 ni R-02.

**Recomendación:** agregar pruebas estructurales: que exista el parámetro de ambiente en ambos pasos y que el validador del diff rechace un cambio fuera de alcance.

### R-09 (Baja). Un `AGENTS.md` global de Codex afecta a todos los proyectos

`docs/uso-skills-codex-cli.md` recomienda un `AGENTS.md` en `%CODEX_HOME%` con rutas absolutas. Ese archivo aplica a todas las sesiones de Codex del equipo. Se pide limitarlo a Oracle/APEX, pero el alcance depende de la redacción.

**Recomendación:** incluir una plantilla exacta y breve en el repositorio en lugar de describirla.

---

## Aspectos correctos verificados

- Corrige la contradicción del navegador (M-05 previo) en `CLAUDE.md`, `AGENTS.md`, `skills/apex/SKILL.md` y `apex-page-automation-safe`.
- `AGENTS.md` ahora lleva la regla que solo tenía `CLAUDE.md`, lo que cubre a Codex.
- El valor predeterminado es el conservador: sin respuesta, se usa segundo plano. Una falla de ruta no autoriza a pasar al navegador.
- La consulta de distribución es de una línea, sin `;`, con binds enteros. Es compatible con `validate_read_only_query`.
- La guía es genérica: no menciona aplicaciones ni páginas concretas, y una prueba lo verifica.
- La tabla de errores conocidos evita repetir rutas fallidas, y el criterio "dos veces con la misma causa" limita los reintentos.
- El registro de decisión está completo (alternativas, riesgos, rollback, descontinuación) y declara que necesita revisión independiente.
- Los enlaces Markdown nuevos resuelven, no hay espacios finales y la CI del PR está en verde.

## Estado de hallazgos previos afectados

| Hallazgo previo | Efecto del PR #32 |
|---|---|
| M-05 contradicciones normativas (navegador) | **Corregido.** Queda abierta la parte del owner `DATA` y de producción sin confirmación |
| M-04 backup de despliegue no reciente | **Mitigado parcialmente** por el export previo (ver R-07) |
| M-03 TOCTOU | **Agravado** para el reordenamiento (ver R-02) |
| M-09 credenciales en variable de entorno | **Ampliado su uso** (ver R-03) |
| A-02 confirmación autodeclarada | Sin cambio: la receta usa `confirmed=true` del agente |
| C-01 visibilidad pública | Según la persona usuaria, ya privado; el contenido sigue en `main` y en el historial |

## Checklist para aprobar el PR #32

- [ ] R-01: ambiente parametrizado en el export y explícito en `deploy_apex_page`, con verificación de que coinciden.
- [ ] R-01: prueba que falle si hay un ambiente fijo o falta `environment`.
- [ ] R-02: validador del diff de distribución y nueva lectura de `last_updated_on` antes del import.
- [ ] R-05: pregunta única alineada en `CLAUDE.md`, el manual y `skills/apex/SKILL.md`.
- [ ] Recomendado: R-03 (`export_apex_page` en el MCP) y R-04 (headless solo para lectura).
- [ ] Actualizar el estado de la decisión con la referencia a esta auditoría.

## Nota sobre ramas de Dependabot

El PR #30 sube `fastmcp` a una versión mayor (`>=4.1.4,<5`). El MCP controlado depende de `FastMCP(...)`, `@mcp.tool(annotations=...)` y `mcp.run(transport="stdio", show_banner=False)`. La CI pasó, pero las pruebas no inician el servidor por stdio **[Inferencial]**. Antes de fusionarlo, conviene validar un *handshake* real (`scripts/validate_apex_controlled_mcp_handshake.py`).
