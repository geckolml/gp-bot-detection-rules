## 1. Compilador

- [x] 1.1 Construir árbol anidado desde la lista prefija (compartido con el intérprete)
- [x] 1.2 Simplificación de constantes y doble negación
- [x] 1.3 Emisión de SQL con umbrales exactos y versión legible redondeada (`evo/to_sql.py`)
- [x] 1.4 Validación de sintaxis con sqlglot (si está instalado)
- [x] 1.5 Escribir con exponente los umbrales de más de 15 dígitos para que DuckDB los lea como `DOUBLE`

## 2. Exportación

- [x] 2.1 Generar modelos dbt de las reglas elegidas (`evo/export_dbt.py`)

## 3. Tests

- [x] 3.1 Test de compilación de reglas conocidas (sin DEAP)
- [x] 3.2 Test de simplificación
- [x] 3.3 Test de equivalencia Python ↔ DuckDB con reglas aleatorias (requiere DuckDB)
- [x] 3.4 Ejecutar los tests y `dbt run --select moderation` dentro del contenedor
- [x] 3.5 Test de equivalencia con umbrales que empatan con valores de los datos (requiere DuckDB)
