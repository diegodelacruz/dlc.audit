# 2026-10-19 Adaptador de ChatGPT sin manifiesto de plugin

Estado: aceptada (pendiente de verificación)

## Contexto

No se obtuvo documentación oficial accesible sobre cómo ChatGPT carga skills personalizadas. La única estructura verificada de plugins es la de Codex (`.codex-plugin/plugin.json`, según `openai/plugins`), que es otra plataforma.

## Decisión

El adaptador de ChatGPT es `plataformas/chatgpt/skills/auditor/SKILL.md`, copia del origen, sin manifiesto. El estado del requisito queda `NO_VERIFICADO` en `docs/cumplimiento/openai.md`.

## Motivo

Inventar un manifiesto con campos no verificados daría una falsa sensación de cumplimiento.

## Consecuencias

- Antes de declarar soporte para ChatGPT hay que verificar su mecanismo y actualizar este adaptador y `plataformas.md`.
