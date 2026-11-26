# 2026-10-19 Adaptador de ChatGPT sin manifiesto de plugin

Estado: Reemplazada por `20261126-multiplataforma-alcance-y-modo.md`

Origen: rama `claude/gallant-babbage-2srymf` (octubre de 2026), portada el 2026-11-26.

## Contexto

No se obtuvo documentación oficial accesible sobre cómo ChatGPT carga skills personalizadas. La única estructura verificada de plugins es la de Codex (`.codex-plugin/plugin.json`, según `openai/plugins`), que es otra plataforma.

## Decisión

El adaptador de ChatGPT es `plataformas/chatgpt/skills/auditor/SKILL.md`, copia del origen, sin manifiesto. El estado del requisito queda `NO_VERIFICADO` en `docs/cumplimiento/openai.md`.

## Motivo

Inventar un manifiesto con campos no verificados daría una falsa sensación de cumplimiento.

## Consecuencias

- Antes de declarar soporte para ChatGPT hay que verificar su mecanismo y actualizar este adaptador y `plataformas.md`.

## Vigencia en dlc.audit (2026-11-26)

ChatGPT se instala subiendo un paquete que genera `python -m dlc_audit skills package`; no se escribe manifiesto. La documentación de ChatGPT ya es accesible (`docs/cumplimiento/openai.md`, O-08), pero no documenta si puede ejecutar Python ni hacer `git push` (O-11): su ejecución sigue **[No verificado]**.
