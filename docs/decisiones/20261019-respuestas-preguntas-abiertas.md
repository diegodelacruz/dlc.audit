# 2026-10-19 Respuestas de Diego a las preguntas abiertas

Estado: Vigente con modificaciones

Origen: rama `claude/gallant-babbage-2srymf` (octubre de 2026), portada el 2026-11-26.

## Decisiones

1. **Alcance de lectura (v1): solo leer.** El auditor lee el código del repositorio auditado y consulta documentación oficial por red. No ejecuta pruebas, scripts ni instalaciones del repositorio auditado. Lo que requiera ejecución se registra como `NO_EJECUTADO` con su motivo.
2. **Escritura del informe: por PR.** Rama nueva y pull request. Nunca en `main` ni en la rama auditada.
3. **Fusión de PR de auditoría: Diego, manualmente.**
4. **Plataformas: obligatorias en v1, con prioridad en Codex.** ChatGPT y Antigravity siguen en v1, pero si una no ofrece mecanismo equivalente se documenta y se propone alternativa. Pendiente: crear el adaptador de Codex con la estructura de plugin verificada en `openai/plugins` (`.codex-plugin/plugin.json`).
5. **Registro de repositorios:** `docs/repositorios.md`, con URL, rama y commit a auditar.

## Salida del informe

El informe es un archivo Markdown con encabezado YAML, según `docs/formato-informe.md`. No se genera HTML ni visualización en v1.

## Pendiente

- Adaptador de Codex (prioridad alta, según la respuesta 4).
- Verificación de los requisitos de ChatGPT y de Antigravity cuando la documentación oficial sea accesible.

## Vigencia en dlc.audit (2026-11-26)

Estado de cada respuesta:

| # | Respuesta de octubre | Hoy |
|---|---|---|
| 1 | Solo leer; lo que requiera ejecución es `NO_EJECUTADO` | Se mantiene que no se ejecuta código ni pruebas del repositorio auditado. Se añade una escritura acotada: ramas `audit/<run_id>` (`20261126-protocolo-auditor-integrador.md`) |
| 2 | Informe por rama nueva y pull request | Reemplazada: no se guardan informes (`20261126-sin-informes-en-este-repositorio.md`); el informe vive en una rama `audit/*` transitoria y en la conversación |
| 3 | Fusión de PR de auditoría: Diego, manualmente | Reemplazada: las ramas de auditoría no se fusionan. La integración a la rama principal la ejecuta el integrador con un prompt, solo si el usuario lo acepta |
| 4 | Plataformas obligatorias en v1, prioridad Codex | Relajada: instalable en las cuatro; ejecución probada donde se pueda (`20261126-multiplataforma-alcance-y-modo.md`) |
| 5 | Registro de repositorios en `docs/repositorios.md` | No portada: el enlace del repositorio llega con cada solicitud y este repositorio no guarda registros de auditorías |

Salida del informe: se mantiene que no se genera HTML; el formato es JSON con documentos generados, no el YAML de octubre.
