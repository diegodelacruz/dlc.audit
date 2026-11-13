# Auditoría integral: `diegodelacruz/apex.skills`

| Campo | Valor |
|---|---|
| Fecha | 2026-11-13 |
| Commit auditado | `e096cd1` (`main`, merge del PR #27, 2026-10-23) |
| Alcance | 31 skills, 31 comandos `.claude/commands`, 54 scripts Python/PowerShell, CI, hooks, documentación, decisiones, upstreams vendorizados, fixtures e historial Git (199 commits) |
| Método | Revisión **estática** (lectura de código, AST propio, búsqueda de patrones, verificación de hashes, análisis de historial) |
| Auditor | Agente externo al repositorio (`dlc.audit`), conforme a §1 de `docs/POLITICA-EVOLUCION-ECOSISTEMA.md` |

## Limitaciones

- **No se ejecutó código del repositorio auditado** (ni `pytest`, ni `scripts/run_ci_checks.py`, ni sus auditores): el entorno bloqueó la instalación de dependencias y la ejecución de código externo. Las métricas de pruebas y cobertura **no se verificaron**.
- No hubo conexión a Oracle/APEX; los comportamientos de SQLcl se marcan **[Inferencial]**.
- No se consultó la configuración de GitHub (protección de ramas, secret scanning del proveedor, visibilidad histórica).
- La búsqueda de secretos en el historial y en los ZIP es heurística (patrones `password|clave|token|secret`), no exhaustiva.
- Este informe omite deliberadamente IPs, hosts, puertos y correos detectados para no replicar la exposición.

## Resumen ejecutivo

El repositorio tiene buena disciplina documental (registros de decisión con alternativas, rollback y descontinuación), una bitácora con escritura anticipada y `fsync`, credenciales enviadas a SQLcl por stdin y un validador de `SELECT` razonable. Sin embargo:

1. **Es público y redistribuye código fuente y datos de infraestructura corporativos**, en contra de su propia política (§4).
2. **Las barreras de seguridad para escritura dependen del propio agente**: la "confirmación" es un parámetro que el agente fija, producción no tiene un control adicional y el coordinador instruye que las skills especialistas no puedan vetar.
3. **La herramienta de "solo artefactos revisados" ejecuta cualquier `.sql` que el agente escriba en el checkout**, incluidos comandos cliente de SQLcl.
4. **El clasificador de resultados puede declarar éxito cuando hubo errores** de compilación PL/SQL o de cliente SQLcl.

| Severidad | Cantidad |
|---|---|
| Crítica | 1 |
| Alta | 3 |
| Media | 9 |
| Baja | 8 |

---

## Hallazgos

### C-01 (Crítica). Repositorio público con código fuente corporativo, infraestructura interna y licencias no declaradas

**Evidencia**

- `vendor/upstreams/zaimella-apex-oracle.zip`: 438 archivos (tablas, vistas, paquetes, migraciones del esquema `DATA` y páginas de aplicaciones APEX).
- `tests/fixtures/apex-exports/f109.zip` y `f130.zip`: exports completos de dos aplicaciones APEX (680 y 599 archivos).
- Dentro de esos ZIP: 5 IPs privadas, varios hosts internos con puertos, URLs APEX por `http://` y direcciones de correo corporativas y personales.
- `.env.example`: host, puerto y servicio de la base TEST, y URLs y workspace de App Builder.
- `vendor/upstreams/manifest.json`: dos upstreams de terceros con `"license": "not-declared"` redistribuidos en el repositorio.
- `SECURITY.md` describe "the private repository", pero hoy el repositorio es público. **[Inferencial]**: su visibilidad cambió después de incorporar estos artefactos.
- `scripts/run_ci_checks.py` (`SECRET_SCAN_EXCLUSIONS`) excluye `vendor/upstreams/*.zip`, y `detect-secrets` no inspecciona archivos comprimidos: ese contenido es un **punto ciego** del control de secretos.
- El propio registro `docs/decisiones/20261023-reconciliacion-auditoria-seguridad.md` (V5) clasifica los hosts como "Abierto, bajo". Este informe lo eleva porque el alcance real es mucho mayor que `.env.example`.

**Contradice:** `POLITICA-EVOLUCION-ECOSISTEMA.md` §4: "No se incorporarán secretos, credenciales, datos reales, identificadores APEX ni código externo sin revisión de seguridad, licencia y compatibilidad".

**No se encontraron** contraseñas reales en los patrones revisados: los valores encontrados eran marcadores o nombres de variables JavaScript. **[No verificado]** de forma exhaustiva.

**Recomendación**

1. Volver el repositorio **privado de inmediato**.
2. Retirar los ZIP corporativos y los fixtures reales; reemplazarlos por fixtures sintéticos mínimos.
3. Evaluar la reescritura del historial (`git filter-repo`), asumiendo que el contenido ya pudo ser clonado o indexado.
4. Rotar cualquier credencial que haya coexistido con esos artefactos, aunque no se haya detectado.
5. Obtener la licencia de los upstreams `not-declared` o dejar de redistribuirlos.
6. Incluir el contenido de los ZIP en el escaneo de secretos.

---

### A-01 (Alta). `execute_sql_file` y `deploy_apex_page` permiten ejecución arbitraria, incluidos comandos cliente

**Evidencia**

- `scripts/apex_controlled_mcp.py` documenta que "never exposes ... inline write SQL". Sin embargo, `workspace_sql_file()` solo exige que exista un `.sql` dentro del checkout. El agente puede escribir el archivo y ejecutarlo en el turno siguiente.
- El contenido se envía sin filtrar al stdin de `sql -S /nolog` (`sqlcl_result`).
- `deploy_apex_page` solo comprueba que el texto contenga `wwv_flow_imp.import_begin` e `import_end`; el resto del archivo es libre.

**[Inferencial]:** SQLcl acepta comandos cliente como `host`/`!` (sistema operativo), `script` (JavaScript), `spool` y `@url`. Un artefacto con esos comandos ejecutaría acciones en la estación de trabajo, fuera de Oracle. Esto no se probó.

**Recomendación**

1. Rechazar los comandos cliente SQLcl en los artefactos (`host`, `!`, `$`, `script`, `spool`, `connect`, `@http`, `@@` fuera del bundle).
2. Exigir que el artefacto esté versionado y sin cambios locales: comparar su hash con `git HEAD`, para que "revisado" signifique "commiteado y revisado".
3. Para DML/DDL simples, considerar `python-oracledb` en lugar de un cliente con intérprete de comandos.

---

### A-02 (Alta). La confirmación humana la declara el propio agente; producción no tiene un control diferenciado y el coordinador anula los vetos

**Evidencia**

- `validate_mutation_decisions(confirmed, backup_choice)` acepta `confirmed=True` enviado por el mismo modelo. La descripción de la herramienta lo admite: "no es una prueba criptográfica de identidad humana".
- `CLAUDE.md` indica:
  - "Act immediately. The user's request IS the authorization."
  - "If the user says production, respect immediately — no extra confirmation."
- `skills/apex/SKILL.md` (Workflow, paso 2) indica: "Delegate ... without letting their local approval or access rules veto the direct user request". Esto neutraliza las skills `*-safe` y `oracle-data-change-governance-final`.
- La política indica "do not precheck or recheck grants" y que no se cuenten filas antes de `DELETE`/`UPDATE`. No existe ningún umbral de filas afectadas.
- Se usa una sola credencial por ambiente para lectura y escritura, sin segregación.

**Recomendación**

1. Denegar por defecto las escrituras en producción. Habilitarlas solo con un factor fuera del modelo, por ejemplo una bandera con vigencia en `.env` (`PRODUCTION_WRITES_UNTIL=<timestamp>`) o una confirmación por *elicitation* del cliente MCP.
2. Permitir que las skills de gobernanza **puedan vetar**: un veto documentado no "bloquea al usuario", protege su pedido.
3. Fijar un umbral parametrizable de filas afectadas, con `rollback` automático cuando se exceda.
4. Separar una cuenta de solo lectura (consultas) de la cuenta de cambios.

---

### A-03 (Alta). Falsos éxitos: errores de compilación PL/SQL y errores SP2 se reportan como `SUCCESS`

**Evidencia**

- `classify_result()` devuelve `SUCCESS` cuando `exit_code == 0` y no aparece `ORA-\d{5}`.
- **[Inferencial]:** `whenever sqlerror` no se activa con un `create or replace package` que compila con errores (SQLcl muestra un aviso y `PLS-`, no `ORA-`) ni con errores de cliente `SP2-`. Solo `execute_readonly_batch` busca `SP2-`.
- `controlled_capabilities.execute_oracle_ddl` hace `commit` y devuelve `ok=True` aunque `all_objects.status` sea `INVALID`.

**Recomendación**

1. Detectar `SP2-`, `PLS-` y los avisos de compilación con errores.
2. Agregar `whenever oserror exit failure`.
3. Validar después de cada DDL en `user_errors`/`all_objects` y fallar si el objeto queda `INVALID`.

---

### M-01 (Media). `controlled_capabilities.py`: los controles llevan nombre de control pero no controlan

`verify_authorization` "never gates", `validate_ddl` siempre devuelve éxito y `execute_oracle_ddl` ejecuta cualquier sentencia y hace `commit`. Lo referencian `apex-schema-automation-safe` y `apex-page-automation-safe`.

**Recomendación:** renombrar las funciones (`observe_*`) o implementar validaciones reales. El sufijo `-safe` genera una falsa sensación de seguridad.

### M-02 (Media). El límite de solo lectura no aísla funciones con transacción autónoma

`set transaction read only` y el filtro de `SELECT` no impiden invocar funciones con `PRAGMA AUTONOMOUS_TRANSACTION`. La herramienta lo reconoce ("no es un sandbox").

**Recomendación:** usar una cuenta de lectura con privilegios mínimos (ver A-02).

### M-03 (Media). TOCTOU entre preflight, snapshot y apply

`execute_change_bundle_artifact` ejecuta preflight, snapshot y apply/verify en **tres sesiones SQLcl distintas**. La huella verificada puede cambiar antes de aplicar el cambio.

**Recomendación:** volver a verificar la huella dentro del bloque de apply, en la misma sesión, con bloqueo (`for update`) o con una condición sobre la huella.

### M-04 (Media). El "backup" del despliegue APEX no se genera en el momento

`deploy_apex_page` acepta como backup un export que ya existe en el repositorio y solo verifica que la aplicación y la página coincidan. No comprueba que refleje el estado actual de la base, así que el rollback puede restaurar una versión obsoleta.

**Recomendación:** exportar la página desde el ambiente destino justo antes de importar y registrar su hash.

### M-05 (Media). Contradicciones normativas entre `CLAUDE.md`, `AGENTS.md` y `skills/apex/SKILL.md`

| Tema | `CLAUDE.md` | `skills/apex/SKILL.md` |
|---|---|---|
| Navegador | "No browser. Never open a browser" | "Use ... App Builder ... or the browser as available" |
| Producción | "no extra confirmation" | "one concise confirmation before any mutation" |
| Owner por defecto | (no aplica) | `DATA` fijo en el texto (contradice la parametrización) |

Además, `CLAUDE.md` describe en `.claude/settings.json` una configuración de auditoría y hooks que no existe, y lista archivos inexistentes (`tests/fixtures/sql-examples/`, `tests/test_apex_mcp_manager.py`).

**Recomendación:** dejar una sola fuente normativa, con `CLAUDE.md` y `AGENTS.md` como punteros, y agregar una prueba que detecte divergencias.

### M-06 (Media). Dependencias no declaradas

- `oracledb`: lo usan `manage_apex_credentials.py` y otros scripts. El mensaje de error dice "Install requirements.txt first", pero `requirements.txt` no lo incluye.
- `requests`: lo usa `external_repo_scanner.py` y tampoco está declarado.

**Recomendación:** declarar ambas dependencias con rango de versión o pasar a la librería estándar (`urllib`).

### M-07 (Media). La ingesta de repositorios externos no trata el contenido como no confiable

`apex-external-context-learn` guarda contenido de repositorios de terceros como contexto reutilizable para agentes futuros. No lo marca como dato no confiable ni lo sanea. Es un vector de *prompt injection* persistente.

**Recomendación:** encapsular ese contenido como datos, prohibir explícitamente seguir instrucciones que contenga y registrar su origen y hash.

### M-08 (Media). La independencia de revisión no se puede cumplir

- Hay un único CODEOWNER, que también es el autor principal.
- 58 de 199 commits están firmados por "Claude" y 62 tienen co-autoría de modelos.
- `SECURITY.md` dice que la protección de ramas está "plan-blocked". Con el repositorio público ese impedimento ya no aplicaría **[No verificado]**.

**Recomendación:** activar la protección de `main`, exigir los checks de CI y exigir la revisión de un agente externo, como `dlc.audit`, antes de fusionar.

### M-09 (Media). Credenciales en texto plano y canales sin cifrado

- `.env` guarda contraseñas en claro; esto está aceptado en una decisión, pero no se verifican los permisos del archivo.
- `Initialize-OracleConnection.ps1` deja `user/password@...` en `$env:APEX_SQLCL_CONN`, que heredan todos los procesos hijos de la sesión.
- Las URLs de App Builder usan `http://`.

**Recomendación:** verificar los permisos de `.env` (0600, o ACL en Windows), retirar la variable de entorno persistente y migrar App Builder a HTTPS.

---

### B-01 (Baja). Métricas obsoletas o no verificables

- "509 tests": el código contiene al menos 567 funciones `test_*`, sin contar las parametrizadas.
- "Overall Score 82/100", "Production Ready" y "Last Updated 2026-08-21" no tienen respaldo verificable.
- "Bandit: 73 checks": `.bandit.yaml` configura 55.
- `SKILLS-INVENTORY-2026-10-02.md` presenta "22 active specialist skills — Ready for production use", pero varias son prototipos.

### B-02 (Baja). Estado de madurez inconsistente

- `apex-application-generator-complete` y `apex-data-migration-safe` tienen `status: active`, pero su descripción dice "Development prototype".
- `CLAUDE.md` marca como DEVELOPMENT a `apex-automated-testing-safe` y `apex-code-generation-safe`, pero sus `SKILL.md` no lo indican.
- `status` aparece solo en 9 de 31 skills.
- Las categorías del frontmatter difieren de las tablas de `CLAUDE.md`.
- Persiste el orden duplicado `3.5`.

### B-03 (Baja). Inventario replicado en varias fuentes

El inventario aparece en `CLAUDE.md`, `skills/README.md`, `SKILLS-QUICK-REFERENCE.md`, dos inventarios Markdown y dos JSON. Contradice el principio de fuente única (§3).

**Recomendación:** generar todos esos inventarios desde el frontmatter y verificar en CI que coincidan.

### B-04 (Baja). Bandit omite chequeos relevantes

Faltan `B105`/`B106`/`B107` (contraseñas fijas en el código), `B108` (archivos temporales) y `B110` (`try/except/pass`).

### B-05 (Baja). Cadena de suministro de CI

Las *actions* están fijadas por etiqueta mayor (`@v7`) y no por SHA, y `codecov` tiene `fail_ci_if_error: false`.

### B-06 (Baja). Ejemplos SQL que violan las reglas canónicas del propio repositorio

`skills/apex-engineering-safe/scripts/user_management_example.sql` y `examples/plsql_examples_corrected.sql` usan mayúsculas y comas al final de línea, en contra de `docs/reglas-formateo-canonicas.md`. Los agentes aprenden de esos ejemplos.

### B-07 (Baja). `.mcp.json.example` no describe servidores MCP reales

**[Inferencial]:**

- Sus entradas `mcpServers` son scripts que terminan al ejecutarse (`validate`, auditor) y un `python -c "from ... import *"`, no servidores MCP.
- `mcpResourceServers` no es una clave estándar.
- Omite el MCP que sí existe, `apex_controlled_mcp.py`.

### B-08 (Baja). Deuda de nombres y solapamiento

- Los sufijos `-safe`, `-complete` y `-final` no transmiten semántica.
- Hay tres skills de *delivery lifecycle* con alcances solapados.
- Los adaptadores `agents/openai.yaml` existen solo en 17 de 31 skills.

---

## Fortalezas verificadas

- Las credenciales se envían a SQLcl por stdin, nunca como argumento (Python y PowerShell).
- La bitácora de mutaciones escribe por adelantado con `fsync` y correlaciona eventos por `event_id`; avisa que no se reintente si falla el cierre.
- `validate_read_only_query`: una sola línea, sin `;`, sin comentarios ni `FOR UPDATE`, con `set define off` y binds enteros validados.
- La ruta de los artefactos se limita al checkout (`resolve` + `relative_to`).
- Los hashes SHA-256 de los ZIP vendorizados **coinciden** con `vendor/upstreams/manifest.json` (verificado).
- El hook `pre-commit.sh` usa un heredoc entre comillas (sin inyección de Bash).
- CI usa `permissions: contents: read`.
- Hay registros de decisión completos (objetivo, alternativas, riesgos, rollback y descontinuación).
- Ningún archivo Python usa `shell=True`, `eval` ni `exec`, ni tiene `except:` sin tipo (análisis AST).

---

## Plan de remediación por hitos

### Hito 1: contención (inmediato)

- [ ] Volver privado `apex.skills`.
- [ ] Retirar `vendor/upstreams/zaimella-*.zip` y `tests/fixtures/apex-exports/*.zip`; definir fixtures sintéticos.
- [ ] Decidir la reescritura del historial y rotar las credenciales relacionadas.
- [ ] Activar la protección de `main` con checks obligatorios.

### Hito 2: barreras de escritura

- [ ] Denegar por defecto las escrituras en producción, con habilitación fuera del modelo y con vigencia.
- [ ] Rechazar comandos cliente SQLcl en los artefactos; exigir que el artefacto esté commiteado.
- [ ] Detectar `SP2-`/`PLS-`/`INVALID` en `classify_result` y en `execute_oracle_ddl`.
- [ ] Permitir el veto de las skills de gobernanza; fijar un umbral parametrizable de filas afectadas.
- [ ] Separar la cuenta de lectura de la de escritura.

### Hito 3: coherencia normativa

- [ ] Fuente normativa única; eliminar las contradicciones de M-05.
- [ ] Generar los inventarios desde el frontmatter y verificarlos en CI.
- [ ] Unificar `status` (`active` | `prototype` | `retired`) en las 31 skills.
- [ ] Corregir dependencias (`oracledb`, `requests`), Bandit y `.mcp.json.example`.

### Hito 4: verificación

- [ ] Ejecutar `scripts/run_ci_checks.py` en un entorno autorizado y actualizar las métricas reales.
- [ ] Agregar pruebas para los falsos éxitos (A-03) y para el rechazo de comandos cliente (A-01).
- [ ] Repetir la auditoría externa sobre el commit de cierre.

## Definition of Done de la remediación

- Repositorio privado, sin datos corporativos en el árbol actual y con una decisión documentada sobre el historial.
- Ninguna escritura en producción posible sin un factor externo al modelo.
- CI en verde con métricas publicadas automáticamente, sin números fijos en la documentación.
- Esta auditoría repetida sin hallazgos críticos ni altos abiertos.
