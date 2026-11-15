-- Velocidad máxima implícita (km/h) entre ubicaciones consecutivas de un
-- usuario dentro de cada ventana horaria. Distancia haversine.
with pings as (
    select
        scenario,
        user_id,
        date_trunc('hour', recorded_at) as window_start,
        recorded_at,
        lat,
        lon,
        lag(lat) over w as prev_lat,
        lag(lon) over w as prev_lon,
        lag(recorded_at) over w as prev_at
    from {{ ref('stg_locations') }}
    window w as (
        partition by scenario, user_id, date_trunc('hour', recorded_at)
        order by recorded_at
    )
),

legs as (
    select
        scenario,
        user_id,
        window_start,
        2 * 6371 * asin(least(1.0, sqrt(
            pow(sin(radians(lat - prev_lat) / 2), 2)
            + cos(radians(prev_lat)) * cos(radians(lat))
              * pow(sin(radians(lon - prev_lon) / 2), 2)
        ))) as dist_km,
        -- mínimo de 1 minuto para evitar divisiones por cero
        greatest(date_diff('second', prev_at, recorded_at), 60) / 3600.0 as dt_hours
    from pings
    where prev_at is not null
)

select
    scenario,
    user_id,
    window_start,
    max(dist_km / dt_hours) as max_geo_speed_kmh
from legs
group by all
