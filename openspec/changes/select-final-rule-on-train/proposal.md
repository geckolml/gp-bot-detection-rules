## Why

Hoy la regla final de cada corrida (`best_rule_id`) se elige con las métricas
del escenario de **prueba**: máximo TPR en prueba entre las reglas con
`FPR ≤ ε` en prueba. Eso tiene dos problemas:

1. **Fuga de información.** El escenario de prueba existe para medir si la
   regla generaliza a un bot que nunca vio. Si además se usa para elegir la
   regla, el resultado reportado es optimista, y la comparación con los
   métodos base (que solo ven entrenamiento) deja de ser justa. En 5 corridas
   de 300 generaciones, la regla elegida mirando la prueba promedió TPR = 0,887
   en prueba y la elegida solo con entrenamiento 0,867.
2. **Reglas poco legibles.** Sin límite de tamaño, la regla de mayor TPR suele
   ser la más grande del frente (40 nodos en la corrida base), lo que contradice
   el objetivo del proyecto: reglas interpretables.

Fase del curso: IV (análisis de la solución óptima y comparación con métodos base).

## What Changes

- La regla final se elige solo con métricas de entrenamiento y con un
  presupuesto de tamaño configurable (`selection.max_size`, por defecto 15 nodos).
- El resumen de la corrida reporta las métricas de esa regla en entrenamiento y
  en prueba. El "mejor TPR en prueba con `FPR ≤ ε`" se conserva como cota
  superior, usada solo para comparar configuraciones en el estudio de sensibilidad.
- La tabla de sensibilidad agrega el TPR en prueba de la regla final.
- La tabla de comparación y la exportación a dbt usan la regla final.

## Capabilities

### New Capabilities
- Ninguna.

### Modified Capabilities
- `rule-evolution`: selección de la regla final.
- `experiment-analysis`: métrica de la regla final en la tabla de sensibilidad.

## Impact

- Código: `evo/run.py`, `evo/sensitivity.py`, `evo/report.py`, `experiments/base.yaml`, tests.
- Cambia qué regla aparece en `summary.json`, `comparison.csv` y en el modelo dbt exportado.
