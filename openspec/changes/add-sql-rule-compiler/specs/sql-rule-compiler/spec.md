## ADDED Requirements

### Requirement: Compilación a SQL
El compilador SHALL traducir cualquier árbol válido a una expresión booleana de
SQL usando `AND`, `OR`, `NOT`, `>` y `<`, con los nombres de las columnas de
`fct_user_activity_hourly` y los umbrales reales de la tabla de cuantiles.

#### Scenario: Regla simple
- **WHEN** se compila `and_(gt(msgs_per_min, q=0.9), lt(reply_rate, q=0.2))` y los cuantiles son 1.5 y 0.05
- **THEN** el resultado es `(msgs_per_min > 1.5) AND (reply_rate < 0.05)`

#### Scenario: Sintaxis válida
- **WHEN** se compila cualquier regla del frente de Pareto
- **THEN** sqlglot la analiza sin errores con el dialecto `duckdb`

### Requirement: Simplificación de constantes
El compilador SHALL eliminar constantes booleanas redundantes y dobles
negaciones sin cambiar el resultado lógico de la regla.

#### Scenario: Constante redundante
- **WHEN** se compila `and_(True, gt(link_ratio, q=0.8))`
- **THEN** el resultado no contiene `TRUE` y equivale a `link_ratio > <cuantil 0.8>`

### Requirement: Equivalencia Python ↔ SQL
Para toda regla, el conjunto de filas que la regla marca al evaluarse en Python
MUST ser idéntico al conjunto de filas que devuelve la consulta SQL compilada
ejecutada en DuckDB sobre los mismos datos.

#### Scenario: Reglas aleatorias
- **WHEN** se generan 50 reglas aleatorias y se evalúan en Python y en DuckDB
- **THEN** las máscaras coinciden fila a fila en las 50 reglas

#### Scenario: Umbral que empata con valores de los datos
- **WHEN** el umbral de una comparación coincide con el valor de la feature en una o más filas y necesita más de 15 dígitos significativos
- **THEN** DuckDB interpreta el literal como `DOUBLE` con el mismo valor que usa Python y las máscaras coinciden fila a fila

### Requirement: Exportación a dbt
El sistema SHALL generar, para las reglas elegidas de una corrida, archivos
`dbt_project/models/moderation/flag_bots_<rule_id>.sql` que seleccionan las filas
marcadas desde `ref('fct_user_activity_hourly')` e incluyen en un comentario
las métricas de la regla.

#### Scenario: Ejecutar reglas exportadas
- **WHEN** se exportan las reglas de una corrida y se ejecuta `dbt run --select moderation`
- **THEN** se crea una tabla por regla con las filas marcadas
