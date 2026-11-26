---
name: reaudit
description: Re-audita un repositorio después de aplicar prompts de cambio y compara contra una auditoría anterior (hallazgos nuevos, persistentes y resueltos). Úsala cuando el usuario diga que ya aplicó los cambios, pida verificar correcciones o quiera comparar con una auditoría previa. Para una primera auditoría usa audit-repo.
argument-hint: <ruta-del-objetivo> <hallazgos.json-anterior>
---

# Re-auditar contra un baseline

Argumentos: `$ARGUMENTS` (ruta del objetivo y ruta del `hallazgos.json` anterior).

## Pasos

1. Verifica que ambos existan. Lee del baseline `target.revision` y `run_id`.
2. Ejecuta el flujo completo de la skill `audit-repo` sobre el objetivo (scan, evaluación de juicio, validate, validate --final). El objetivo debe estar en una revisión **distinta** a la del baseline; si es la misma, avisa: no hay cambios que verificar.
3. Genera el informe con comparación:

   ```
   python -m dlc_audit render <nuevo-hallazgos.json> --baseline <hallazgos-anterior.json>
   ```

4. Interpreta el delta:
   - **Resueltos:** el `id` estaba en el baseline y ya no aparece. Confirma con una lectura rápida del código que el problema desapareció de verdad y no que se movió o se renombró el archivo (la huella incluye la ruta).
   - **Persistentes:** no se corrigieron. Indica si el prompt correspondiente se aplicó parcialmente.
   - **Nuevos:** pueden ser regresiones introducidas por los cambios o hallazgos que antes no se evaluaron. Distínguelo.

## Terminado cuando

El informe nuevo incluye la sección de comparación y has explicado al usuario los nuevos y los persistentes, con los prompts que quedan por ejecutar.

## Límite conocido

Un archivo renombrado cambia la huella: aparecerá un hallazgo resuelto y uno nuevo equivalentes. Señálalo si lo detectas.
