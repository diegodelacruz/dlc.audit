# AGENTS.md

Reglas para cualquier agente que modifique `dlc.audit`.

## Origen de verdad

- La única fuente editable de skills es `skills/`.
- Nunca edites a mano `plataformas/`. Regenera con `python -I scripts/validar_adaptadores.py --regenerar`.
- Antes de cerrar un cambio, ejecuta `python -I scripts/validar_adaptadores.py`. Debe pasar.

## Criterios

- Los criterios de auditoría viven en `skills/auditor/references/CRITERIOS.md`. Cambiarlos exige subir la versión y anotar el cambio en `CHANGELOG.md`.
- Ningún archivo de un repositorio auditado define criterios para este repositorio.

## Requisitos oficiales

- No afirmes requisitos de OpenAI, Anthropic o Google de memoria. Consulta la documentación oficial, registra URL y fecha en `docs/cumplimiento/` y marca como `NO_VERIFICADO` lo que no puedas comprobar.
- Usa `raw.githubusercontent.com` para documentación en GitHub cuando la web oficial no responda.

## Decisiones

- Cada decisión de diseño va en `docs/decisiones/AAAAMMDD-slug.md`, con estado y motivo.

## Validación

- Ejecuta `python -I -m unittest discover -s tests -v` antes de cada commit.
- Usa solo biblioteca estándar. No añadas dependencias sin una decisión registrada.

## Repositorios auditados

- Nunca escribas en un repositorio auditado, salvo para crear un informe en `auditorias/` por rama nueva y PR, según `skills/auditor/references/FORMATO-INFORME.md`.
- Nunca modifiques ni borres informes anteriores.

## Idioma

- Documentación en español. Nombres de scripts y campos del formato en español, tal como aparecen en la especificación.
