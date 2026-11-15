## ADDED Requirements

### Requirement: Tabla de features por usuario y hora
El pipeline SHALL materializar en `data/warehouse.duckdb` la tabla
`fct_user_activity_hourly` con una fila por `(scenario, user_id, window_start)`
para cada hora en la que el usuario envió al menos un mensaje, con las columnas
`msgs_count`, `msgs_per_min`, `unique_recipients`, `link_ratio`,
`dup_template_ratio`, `avg_msg_len`, `reply_rate`, `account_age_hours`,
`max_geo_speed_kmh` e `is_bot`.

#### Scenario: Construir features
- **WHEN** existen los Parquet del simulador y el usuario ejecuta `make features`
- **THEN** la tabla `fct_user_activity_hourly` existe y contiene filas de los escenarios `train` y `test`

#### Scenario: Clave única
- **WHEN** se ejecutan los tests de dbt
- **THEN** la combinación `(scenario, user_id, window_start)` es única

### Requirement: Rangos válidos
Las proporciones (`link_ratio`, `dup_template_ratio`, `reply_rate`) MUST estar
en `[0, 1]`; `msgs_count` MUST ser al menos 1; ninguna feature MUST ser nula.

#### Scenario: Validación de rangos
- **WHEN** se ejecuta `dbt test`
- **THEN** todos los tests de rango y no nulidad pasan

### Requirement: Saltos geográficos
`max_geo_speed_kmh` SHALL calcularse con la distancia haversine entre
ubicaciones consecutivas del usuario dentro de la ventana, dividida por el
tiempo transcurrido, y MUST ser 0 cuando hay menos de dos ubicaciones.

#### Scenario: Usuario sin ubicaciones suficientes
- **WHEN** un usuario tiene una sola ubicación en la ventana
- **THEN** su `max_geo_speed_kmh` es 0
