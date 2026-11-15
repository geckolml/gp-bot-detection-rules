# Notebooks

Solo para análisis y narrativa del informe. La lógica vive en los módulos de
Python (`evo/`, `baselines/`, `simulator/`); los notebooks leen
`results/runs/`, `results/tables/`, `results/figures/` y `data/warehouse.duckdb`.

- `01_analisis.ipynb`: problema y datos, diseño del algoritmo, convergencia,
  ablación, sensibilidad, regla final, costo de la legibilidad, comparación con
  métodos base y conclusiones. Las frases con cifras se calculan en las celdas
  de código.

Para volver a ejecutarlo con los resultados actuales: `make analysis`.
Para abrirlo: `make notebook` → http://localhost:8888
