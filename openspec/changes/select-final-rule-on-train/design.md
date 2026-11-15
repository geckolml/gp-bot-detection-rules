## Context

Costo de la legibilidad en la corrida base (150 generaciones, semilla 42).
Cada fila es la regla de mayor TPR en entrenamiento con `FPR ≤ 2 %` en
entrenamiento y a lo sumo ese número de nodos:

| Máximo de nodos | Nodos | TPR entrenamiento | TPR prueba | FPR prueba | TPR bot sigiloso |
|---|---|---|---|---|---|
| 3 | 3 | 0,875 | 0,697 | 0,015 | 0,08 |
| 7 | 7 | 0,953 | 0,798 | 0,012 | 0,29 |
| 11 | 11 | 0,977 | 0,836 | 0,017 | 0,38 |
| 15 | 15 | 0,983 | 0,832 | 0,017 | 0,34 |
| 23 | 23 | 0,990 | 0,845 | 0,016 | 0,39 |
| sin límite | 40 | 0,993 | 0,879 | 0,017 | 0,52 |

## Decisions

### Elegir solo con entrenamiento
`select_final_rule(rules, fpr_max, max_size)` devuelve la regla de mayor TPR en
entrenamiento entre las que cumplen `FPR ≤ ε` en entrenamiento y tienen a lo
sumo `max_size` nodos (tamaño de la regla simplificada). Empates: menos nodos.
Las métricas de prueba no participan. Es el mismo criterio con el que la
regresión logística elige su umbral, así que la comparación es simétrica.

Alternativa descartada: separar una parte del entrenamiento como validación.
Sería lo habitual con un modelo de muchos parámetros, pero aquí la regla tiene
pocos nodos y la restricción ya se evalúa en 40 000 filas; agregaría un
parámetro más sin cambiar la conclusión.

### Presupuesto de tamaño
`selection.max_size: 15` (hasta 4 comparaciones). El frente de Pareto sigue
ofreciendo todas las reglas; el presupuesto solo fija cuál se reporta y se
exporta. `null` desactiva el límite. La tabla de arriba se incluye en el
análisis como "costo de la legibilidad".

### Resumen de la corrida
`summary.json` incluye de la regla final: `best_rule_id`, `best_size`,
`best_train_tpr`, `best_train_fpr`, `best_test_tpr`, `best_test_fpr` y
`best_sql_readable`. Se conserva `best_test_tpr_feasible` con su significado
actual (cota superior mirando la prueba).

### Sensibilidad
`sensitivity.csv` agrega `tpr_final_test_mean` y `tpr_final_test_std`,
calculadas desde `pareto.json` con la misma función de selección, y la figura
de sensibilidad de TPR usa esa métrica.

### Agrupación de corridas en el reporte
Las bandas de convergencia agrupan corridas con las mismas secciones
`algorithm`, `fitness` y `data`. Las secciones que no afectan a la evolución
(`selection`, `lcs`, `parallel`) no separan grupos.

## Risks / Trade-offs

- [La regla elegida puede violar `FPR ≤ ε` en prueba] → se reporta tal cual; es
  información sobre cuánto generaliza la restricción.
- [El presupuesto de 15 nodos es una convención] → es configurable y el
  análisis muestra la curva completa.
