select
    regexp_extract(filename, '([^/\\]+)[/\\][^/\\]+\.parquet$', 1) as scenario,
    message_id,
    sender_id,
    recipient_id,
    cast(sent_at as timestamp) as sent_at,
    has_link,
    msg_len,
    template_id
from {{ source('raw', 'messages') }}
