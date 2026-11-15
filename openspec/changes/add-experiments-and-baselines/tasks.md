## 1. Métodos base

- [x] 1.1 Carga de features de entrenamiento y prueba desde DuckDB (compartida con `evo`)
- [x] 1.2 Regla manual de experto
- [x] 1.3 Árbol de decisión (profundidad 3 y 5) y su exportación a SQL
- [x] 1.4 Regresión logística con umbral restringido a `FPR ≤ ε`
- [x] 1.5 CLI `python -m baselines.run_baselines` que escribe `results/tables/baselines.csv`
- [x] 1.6 Adaptar el LCS del cuaderno del curso (`baselines/lcs.py`)
- [x] 1.7 Corrida de un objetivo (`make evolve-single`) y su fila `gp_single` en la tabla de comparación

## 2. Sensibilidad

- [x] 2.1 `experiments/sensitivity.yaml` con diseño uno a la vez y 5 semillas
- [x] 2.2 Runner `python -m evo.sensitivity` que expande la grilla y ejecuta las corridas
- [x] 2.3 Agregación en `results/tables/sensitivity.csv`

## 3. Figuras

- [x] 3.1 Convergencia con bandas entre semillas (`evo/plots.py`)
- [x] 3.2 Hipervolumen por generación
- [x] 3.3 Frente de Pareto con métodos base
- [x] 3.4 Sensibilidad por parámetro
- [x] 3.5 Comparación entrenamiento vs prueba
- [x] 3.6 CLI `python -m evo.report` (`make report`)

## 4. Tests y verificación

- [x] 4.1 Test de expansión de la grilla uno a la vez
- [x] 4.2 Test del umbral restringido de la regresión logística
- [x] 4.3 Ejecutar `make sensitivity`, `make baselines` y `make report` en el contenedor
- [x] 4.4 Notebook `notebooks/01_analisis.ipynb` con la narrativa del informe usando las figuras generadas
