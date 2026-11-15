## 1. Proyecto dbt

- [x] 1.1 Crear `dbt_project.yml` y `profiles.yml` (DuckDB local)
- [x] 1.2 Definir fuentes externas sobre los Parquet de todos los escenarios (`sources.yml`)

## 2. Modelos

- [x] 2.1 Modelos de staging: `stg_users`, `stg_messages`, `stg_locations`
- [x] 2.2 Modelo intermedio `int_geo_speed` (haversine entre ubicaciones consecutivas)
- [x] 2.3 Modelo `fct_user_activity_hourly` con las 9 features y la etiqueta

## 3. Tests

- [x] 3.1 Tests de no nulidad y clave única en `schema.yml`
- [x] 3.2 Tests de rango para proporciones y `msgs_count`
- [x] 3.3 Verificar `make features` y `dbt test` dentro del contenedor
