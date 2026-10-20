# 2026-10-19 Respuestas de Diego a las preguntas abiertas

Estado: aceptada

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
