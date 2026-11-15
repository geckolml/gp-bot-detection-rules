## Decisions

### Recorrido compartido con el evaluador
El compilador recorre la misma lista prefija que el intérprete de
`evo/tree_eval.py`. Solo necesita de cada nodo `name`, `arity` y `value`, por
lo que funciona con árboles de DEAP y con nodos de prueba sin DEAP.

### Umbrales exactos
`gt(f, q)` se compila como `f > <valor>` donde `<valor>` es el cuantil `q` de
`f` en entrenamiento, escrito con `repr` de Python (representación más corta
que conserva el mismo `double`). Así DuckDB compara contra exactamente el mismo
número que numpy. Para el informe se genera además una versión legible con
umbrales redondeados, marcada como no equivalente.

DuckDB interpreta un literal con punto y sin exponente (`45.333333333333336`)
como `DECIMAL` y lo convierte a `DOUBLE` al comparar. Con más de 15 dígitos
significativos esa conversión puede cambiar el último bit (medido en DuckDB
1.5: 2,2 % de los valores), y entonces una fila cuyo valor empata con el umbral
queda marcada en SQL pero no en Python, o al revés. Los empates son frecuentes
porque varias features son promedios o proporciones de enteros. Por eso los
umbrales con más de 15 dígitos se escriben con exponente
(`45.333333333333336e0`), que DuckDB lee directamente como `DOUBLE`. Los
umbrales cortos (`1.5`, `0.05`) se dejan sin exponente: con 15 dígitos o menos
la conversión es exacta.

### Simplificación
Reglas de reescritura aplicadas de abajo hacia arriba:
`True AND x → x`, `False AND x → False`, `True OR x → True`,
`False OR x → x`, `NOT True → False`, `NOT False → True`, `NOT NOT x → x`.
La simplificación es lógicamente equivalente, por lo que no rompe la prueba de
equivalencia.

### Modelo dbt generado
```sql
-- regla: <run_id>/<rule_id> | train TPR=… FPR=… | test TPR=… FPR=… | nodos=…
select scenario, user_id, window_start, '<rule_id>' as rule_id
from {{ ref('fct_user_activity_hourly') }}
where <expresión>
```

### Validación
- Sintaxis: `sqlglot.parse_one(expr, read="duckdb")` no lanza error.
- Equivalencia: para un conjunto de reglas (aleatorias y del frente de Pareto),
  la máscara de Python y el resultado de la consulta en DuckDB coinciden fila a fila.
