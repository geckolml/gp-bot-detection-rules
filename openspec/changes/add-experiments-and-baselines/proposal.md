## Why

El enunciado da el mayor peso a la fase de Análisis y Conclusiones: curvas de
convergencia, estudio de sensibilidad de parámetros, análisis de la mejor
solución y comparación con métodos de referencia. Este cambio agrega todo lo
necesario para producir esa evidencia de forma reproducible.

Fase del curso: III (ejecución y estudio de sensibilidad) y IV (análisis).

## What Changes

- Métodos de referencia en `baselines/`: regla manual escrita por un experto,
  árbol de decisión, regresión logística y un Learning Classifier System basado
  en el cuaderno del curso.
- Runner del estudio de sensibilidad que expande una grilla de parámetros con
  varias semillas.
- Módulo de gráficos: convergencia, frente de Pareto contra métodos base y
  mapas de calor de sensibilidad.
- Tabla comparativa final (entrenamiento vs prueba) para el informe y el README.

## Capabilities

### New Capabilities
- `baselines`: métodos de referencia evaluados con las mismas métricas.
- `experiment-analysis`: estudio de sensibilidad, agregación de corridas y gráficos.

### Modified Capabilities
- Ninguna.

## Impact

- Código nuevo: `baselines/run_baselines.py`, `evo/sensitivity.py`,
  `evo/plots.py`, `evo/report.py`, `experiments/sensitivity.yaml`.
- Figuras en `results/figures/` y tablas en `results/tables/`.
