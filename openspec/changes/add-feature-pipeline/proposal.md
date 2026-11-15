## Why

Las reglas evolucionadas operan sobre variables de comportamiento agregadas por
usuario y ventana de tiempo. Calcularlas con dbt sobre DuckDB hace que la misma
tabla de features alimente la evolución y la ejecución de las reglas en SQL, y
conecta el proyecto con prácticas de ingeniería de datos.

Fase del curso: I (variables de decisión del modelo) y III (implementación).

## What Changes

- Proyecto dbt en `dbt_project/` con perfil DuckDB local.
- Fuentes que leen los Parquet del simulador de todos los escenarios.
- Modelos de staging y el modelo `fct_user_activity_hourly` con 9 variables de
  comportamiento por usuario y hora.
- Tests de dbt (no nulos, unicidad, rangos).

## Capabilities

### New Capabilities
- `feature-pipeline`: tabla de features por usuario y ventana horaria en DuckDB.

### Modified Capabilities
- Ninguna.

## Impact

- Código nuevo: `dbt_project/` (modelos, `sources.yml`, `schema.yml`, `profiles.yml`).
- Base de datos `data/warehouse.duckdb` (no versionada).
- Es la entrada de `rule-evolution`, `baselines` y `sql-rule-compiler`.
