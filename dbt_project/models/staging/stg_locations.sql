select
    regexp_extract(filename, '([^/\\]+)[/\\][^/\\]+\.parquet$', 1) as scenario,
    user_id,
    cast(recorded_at as timestamp) as recorded_at,
    lat,
    lon
from {{ source('raw', 'locations') }}
