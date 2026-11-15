## Why

Es el núcleo del trabajo: un algoritmo evolutivo que encuentra reglas lógicas
interpretables para detectar bots, balanceando detección, falsos positivos y
simplicidad de la regla.

Fase del curso: II (diseño del algoritmo evolutivo) y III (implementación).

## What Changes

- Programación Genética tipada (STGP) con DEAP en `evo/`.
- Conjunto de primitivas lógicas y de comparación con umbrales expresados como
  cuantiles de cada feature.
- Dos modos de optimización: multiobjetivo (NSGA-II) y un objetivo con
  penalización (para comparar).
- Restricción de tasa de falsos positivos tratada por penalización.
- Registro por generación (logbook) y frente de Pareto final por corrida.
- CLI configurada por YAML.

## Capabilities

### New Capabilities
- `rule-evolution`: evolución de reglas de detección con Programación Genética.

### Modified Capabilities
- Ninguna.

## Impact

- Código nuevo: `evo/primitives.py`, `evo/tree_eval.py`, `evo/fitness.py`,
  `evo/algorithms.py`, `evo/run.py`, `experiments/base.yaml`.
- Resultados en `results/runs/<run_id>/`.
- Depende de `feature-pipeline`; alimenta a `sql-rule-compiler` y `experiment-analysis`.
