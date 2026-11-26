# dlc.audit

Auditor **externo e independiente** para un flujo de dos roles:

- **Integrador:** el agente que construye, modifica y corrige repositorios.
- **Auditor (este repositorio):** valida lo que hizo el integrador, sin ser juez y parte.

Recibe el **enlace** de un repositorio, lo audita, publica una rama `audit/<run_id>` con las observaciones y te entrega un prompt para el integrador. Cuando el integrador termina, te entrega un prompt de cierre que pegas aquí, y el auditor verifica y vuelve a auditar. Cada ronda son **dos pegados**.

```
Tú -> [enlace] -> AUDITOR -> prompt A -> Tú -> INTEGRADOR -> prompt B (cierre) -> Tú -> AUDITOR -> dictamen
```

Detalle y garantías: [docs/protocolo.md](docs/protocolo.md).

> **Estado:** v1 incompleta. El núcleo y el protocolo funcionan con Claude Code; la compatibilidad con Codex, ChatGPT y Antigravity (obligatoria en v1) está pendiente. Ver [docs/alcance.md](docs/alcance.md).

## Qué audita (Fase 1)

| Dominio | Ejemplos de reglas |
|---|---|
| Transversal | Secretos, README, CHANGELOG, `.gitignore`, pruebas y CI, valores fijos de entorno |
| Skills y agentes de Claude | Frontmatter, nombres, descripciones, herramientas del subagente, permisos, enlaces rotos |
| SQL, PL/SQL y APEX | Formato, SQL dinámico, `when others then null`, idempotencia, auditoría, parametrización |
| Python, FastAPI, Glue | Dependencias, excepciones, SQL interpolado, rutas S3 fijas, llamadas peligrosas |

El catálogo completo está en `rules/*.json` (38 reglas). Qué queda fuera: `docs/alcance.md`.

## Requisitos

- Python 3.11 o superior (python.org). Sin dependencias externas.
- Git en el `PATH`.
- Una plataforma de agentes con shell: Claude Code, Codex, Antigravity o ChatGPT con Skills. Ver [Plataformas](#plataformas).

## Plataformas

Las skills siguen el estándar abierto *Agent Skills*. Se abre la plataforma **dentro de un clon de este repositorio** y descubre las skills sola.

| Plataforma | Dónde las encuentra | Estado |
|---|---|---|
| Claude Code | `.claude/skills/` | Probable de punta a punta (L2) |
| Codex | `.agents/skills/` | Instalable (L1). Ejecución **[No verificado]** |
| Antigravity | `.agents/skills/` | Instalable (L1). Ejecución **[No verificado]** |
| ChatGPT | Subida del paquete `python -m dlc_audit skills package` | Instalable (L1). Ejecución **[No verificado]**; exige un plan con Skills habilitadas |

Detalle, fuentes y límites: [docs/multiplataforma.md](docs/multiplataforma.md). La fuente única es `skills/`; las copias en `.claude/skills/` y `.agents/skills/` se generan con `python -m dlc_audit skills sync` y **no se editan a mano**.

## Uso

### Ronda 1

En la plataforma, dentro de este repositorio (en Claude Code se invoca como `/audit-repo`):

```
/audit-repo https://github.com/<usuario>/<repositorio> [rama-o-commit]
```

El auditor clona, audita, valida, genera informe y prompts, publica la rama `audit/<run_id>` y te devuelve el **prompt A**. Cada prompt trae su indicación `CONVERSACIÓN: MISMA` o `NUEVA`. Pega el prompt A en el integrador.

### Cierre del integrador y ronda 2

El integrador responde con el **prompt B** (cierre). Pégalo en el auditor:

```
/reaudit
<pega aquí el cierre completo>
```

El auditor verifica lo declarado contra el repositorio, audita todo de nuevo, compara con la ronda anterior y emite el dictamen. Si no es `APROBADO`, te entrega un nuevo prompt A.

### Cierre del ciclo

Con `APROBADO`, el auditor **elimina las ramas `audit/*` del ciclo**, te **pregunta si genera el prompt de merge** a la rama principal y, al terminar, **purga sus archivos de trabajo**. El merge lo ejecuta el integrador con ese prompt; el auditor no modifica nada más del repositorio auditado.

> **Este repositorio no guarda informes de auditoría, bajo ningún concepto.** Los archivos de trabajo van al directorio temporal del sistema (`python -m dlc_audit workdir`), el código rechaza cualquier ruta dentro de este repositorio y el informe final solo queda en la conversación. Una prueba automática lo verifica.

### Manual (sin skills)

```
python -m dlc_audit fetch <url> [--ref <rama>]
python -m dlc_audit scan <ruta-clon> --ref <rama>
# evaluar reglas pending (agente dlc-auditor) y completar executive_summary
python -m dlc_audit validate <hallazgos.json> --assign-ids
python -m dlc_audit validate <hallazgos.json> --final
python -m dlc_audit render <hallazgos.json>
python -m dlc_audit publish <hallazgos.json> --push
# ronda 2
python -m dlc_audit closure --baseline <baseline.json> --cierre <cierre.json> --repo <ruta-clon>
python -m dlc_audit scan <ruta-clon> --ref <rama> --baseline <baseline.json>
# cierre del ciclo (dictamen APROBADO)
python -m dlc_audit cleanup <final.json> --repo <ruta-clon>            # simulación
python -m dlc_audit cleanup <final.json> --repo <ruta-clon> --delete   # borra audit/*; no guarda registros
python -m dlc_audit merge-prompt <final.json> --repo <ruta-clon>       # solo si aceptas
python -m dlc_audit purge <nombre-repo>                                 # último paso: borra archivos de trabajo
# skills
python -m dlc_audit skills check                                        # portabilidad y sincronía
python -m dlc_audit skills sync                                         # regenera las copias desde skills/
```

Requisito: permiso de **escritura** en el repositorio auditado, solo para crear y borrar ramas `audit/<run_id>`.

## Garantías de diseño

- **No se modifica nada del repositorio auditado.** Solo se crean ramas `audit/<run_id>` (con archivos bajo `.audit/<run_id>/`) y, al aprobar, se borran las del ciclo. `publish` aborta si el diff toca otra ruta; `cleanup` aborta si una rama contiene otra cosa; nunca hay force push ni merge de ramas de auditoría.
- **El cierre del integrador se verifica, no se cree:** commits, archivos, deriva (cambios no declarados) y correcciones declaradas que siguen presentes.
- **Dictamen explícito** y configurable (`approval` en el perfil).
- **Prompts autosuficientes** con indicación `MISMA` o `NUEVA` conversación (`handoff` en el perfil).
- **Evidencia verificada:** `validate` comprueba que cada cita exista en el archivo real; una cita inventada se rechaza.
- **Certeza explícita:** `verified`, `inferential` (**[Inferencial]**), `unverified` (**[No verificado]**).
- **Secretos redactados** en informe y prompts.
- **Idempotente:** mismo objetivo y revisión producen los mismos ids de hallazgo.
- **Parametrizado:** reglas versionadas y con vigencia en `rules/`; perfiles en `profiles/`.

## Estructura

```
AGENTS.md                reglas para agentes
docs/                    protocolo, alcance, contrato de salida, metodología
rules/                   catálogos de reglas (JSON, versionados)
profiles/                perfiles: catálogos, severidades, convenciones de prompts
templates/               plantillas de informe y de prompts (integrador y detalle)
dlc_audit/               scan, validate, render, fetch, publish, closure, skills (Python, solo biblioteca estándar)
skills/                  fuente única de las skills portables (audit-repo, reaudit)
.claude/skills/          copia generada para Claude Code (no editar)
.agents/skills/          copia generada para Codex y Antigravity (no editar)
.claude/agents/          subagente opcional dlc-auditor (solo Claude Code)
tests/                   pruebas (unittest)
```

## Pruebas

```
python -m unittest discover -s tests
```

## Documentación

- [Protocolo auditor-integrador](docs/protocolo.md)
- [Multiplataforma](docs/multiplataforma.md)
- [Cumplimiento de plataformas (fuentes y citas)](docs/cumplimiento/plataformas.md)
- [Registro de decisiones](docs/decisiones/README.md)
- [Criterios de octubre y su estado](docs/criterios.md)
- [Alcance y fases](docs/alcance.md)
- [Contrato de salida](docs/contrato-salida.md)
- [Metodología](docs/metodologia.md)
- [Changelog](CHANGELOG.md)
