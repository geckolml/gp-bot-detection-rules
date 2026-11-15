## Context

El simulador escribe `data/raw/<escenario>/{users,messages,locations}.parquet`.
DuckDB lee Parquet directamente, así que no hace falta una etapa de carga.

## Decisions

### Granularidad: usuario × hora
Cada fila es un usuario en una ventana de una hora en la que envió al menos un
mensaje. Es el mismo grano con el que la regla se ejecutaría en producción
(un modelo dbt que corre cada hora). La etiqueta `is_bot` se hereda del usuario.

### Features

| Columna | Definición | Señal |
|---|---|---|
| `msgs_count` | mensajes enviados en la ventana | volumen |
| `msgs_per_min` | `msgs_count / 60` | ritmo |
| `unique_recipients` | destinatarios distintos | difusión masiva |
| `link_ratio` | proporción de mensajes con link | spam |
| `dup_template_ratio` | `1 - plantillas distintas / mensajes` | texto repetido |
| `avg_msg_len` | longitud promedio | mensajes cortos tipo plantilla |
| `reply_rate` | proporción de destinatarios de la ventana que alguna vez respondieron | reciprocidad |
| `account_age_hours` | horas desde la creación de la cuenta al inicio de la ventana | cuentas nuevas |
| `max_geo_speed_kmh` | máxima velocidad implícita entre ubicaciones consecutivas de la ventana (0 si hay menos de 2) | saltos imposibles |

### Escenarios en una sola tabla
Las fuentes usan `read_parquet('data/raw/*/<tabla>.parquet', filename = true)`
y extraen el escenario de la ruta. La clave de la tabla es
`(scenario, user_id, window_start)`.

### Perfil DuckDB
`profiles.yml` dentro de `dbt_project/` con `path: ../data/warehouse.duckdb`
relativo, para que funcione igual en el contenedor y en local.

## Risks / Trade-offs

- [`reply_rate` usa respuestas posteriores a la ventana (fuga de información
  futura)] → aceptable para el curso; documentado como limitación. En
  producción se calcularía con respuestas hasta el final de la ventana.
