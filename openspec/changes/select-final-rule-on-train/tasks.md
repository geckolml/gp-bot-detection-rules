## 1. Selección

- [x] 1.1 Función `select_final_rule` (solo entrenamiento, presupuesto de tamaño) en `evo/run.py`
- [x] 1.2 Parámetro `selection.max_size` en `experiments/base.yaml` y campos de la regla final en `summary.json`
- [x] 1.3 Test: la prueba no interviene en la elección
- [x] 1.4 Test: presupuesto de tamaño y caso sin regla factible

## 2. Experimentos y reporte

- [x] 2.1 Columnas `tpr_final_test_mean` / `tpr_final_test_std` en `sensitivity.csv` y en la figura de sensibilidad
- [x] 2.2 Agrupar corridas para la convergencia solo por `algorithm`, `fitness` y `data`
- [x] 2.3 Test de las columnas nuevas de la tabla de sensibilidad

## 3. Verificación

- [x] 3.1 `make test` y `openspec validate --all`
- [x] 3.2 Repetir `make evolve` y `make report`; exportar la regla final a dbt y comprobar que marca las mismas filas que en Python
