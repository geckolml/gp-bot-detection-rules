select
    regexp_extract(filename, '([^/\\]+)[/\\][^/\\]+\.parquet$', 1) as scenario,
    user_id,
    agent_type,
    is_bot,
    cast(created_at as timestamp) as created_at
from {{ source('raw', 'users') }}
