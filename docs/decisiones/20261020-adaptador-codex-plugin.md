# 2026-10-20 Adaptador de Codex como plugin

Estado: aceptada

## Contexto

Diego pidió que Codex sea la prioridad entre las plataformas (respuesta 4). Codex carga skills desde un plugin con `.codex-plugin/plugin.json` y una carpeta `skills/` al lado (ver `docs/cumplimiento/openai.md`, O-02).

La fuente verificada es el ejemplo `plugins/figma/.codex-plugin/plugin.json` del repositorio `openai/plugins`, leído el 2026-10-20. La guía oficial de build (`developers.openai.com/codex/plugins/build`) no fue accesible desde el entorno.

## Decisión

- El manifiesto `plataformas/codex/.codex-plugin/plugin.json` se escribe a mano con un conjunto mínimo de campos: `name`, `version`, `description`, `repository`, `skills` (`./skills/`) e `interface` (`displayName`, `shortDescription`, `capabilities`).
- Se omiten campos del ejemplo que no son necesarios para el auditor: `author`, `license`, `keywords`, `apps`, `defaultPrompt`, `category` y otros.
- La carpeta `skills/auditor/` es copia generada de `skills/`, igual que los demás adaptadores.
- `scripts/validar_adaptadores.py` comprueba que el manifiesto exista, sea JSON válido, tenga `name` y apunte a `./skills/`.

## Motivo

Es el mecanismo más cercano verificado para cargar la skill en Codex, y es la prioridad declarada.

## Consecuencias

- Los campos del manifiesto se verifican solo contra un ejemplo. [No verificado] que el conjunto mínimo sea completo. Cuando la guía de build sea accesible, hay que revisar este manifiesto y registrar el resultado en `docs/cumplimiento/openai.md`.
- No se generó marketplace (`.agents/plugins/marketplace.json`). La instalación es manual copiando la carpeta del plugin, hasta que se decida publicarlo.
