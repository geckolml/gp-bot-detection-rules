-- Una fila por usuario y hora en la que envió al menos un mensaje.
-- Es el grano sobre el que evolucionan y se ejecutan las reglas.
with msgs as (
    select *, date_trunc('hour', sent_at) as window_start
    from {{ ref('stg_messages') }}
),

-- Primer contacto de cada par remitente -> destinatario
pair_first as (
    select scenario, sender_id, recipient_id, min(sent_at) as first_at
    from msgs
    group by all
),

-- Pares en los que el destinatario respondió después del primer contacto
replied_pairs as (
    select p.scenario, p.sender_id, p.recipient_id
    from pair_first p
    join msgs r
      on r.scenario = p.scenario
     and r.sender_id = p.recipient_id
     and r.recipient_id = p.sender_id
     and r.sent_at >= p.first_at
    group by all
),

window_pairs as (
    select distinct scenario, sender_id, recipient_id, window_start
    from msgs
),

reply_by_window as (
    select
        w.scenario,
        w.sender_id as user_id,
        w.window_start,
        avg(case when rp.sender_id is not null then 1.0 else 0.0 end) as reply_rate
    from window_pairs w
    left join replied_pairs rp
      on rp.scenario = w.scenario
     and rp.sender_id = w.sender_id
     and rp.recipient_id = w.recipient_id
    group by all
),

activity as (
    select
        scenario,
        sender_id as user_id,
        window_start,
        count(*) as msgs_count,
        count(distinct recipient_id) as unique_recipients,
        avg(cast(has_link as double)) as link_ratio,
        1 - count(distinct template_id) / count(*)::double as dup_template_ratio,
        avg(cast(msg_len as double)) as avg_msg_len
    from msgs
    group by all
)

select
    a.scenario,
    a.user_id,
    a.window_start,
    cast(a.msgs_count as double) as msgs_count,
    a.msgs_count / 60.0 as msgs_per_min,
    cast(a.unique_recipients as double) as unique_recipients,
    a.link_ratio,
    a.dup_template_ratio,
    a.avg_msg_len,
    r.reply_rate,
    date_diff('second', u.created_at, a.window_start) / 3600.0 as account_age_hours,
    coalesce(g.max_geo_speed_kmh, 0.0) as max_geo_speed_kmh,
    u.is_bot,
    u.agent_type
from activity a
join reply_by_window r
  on r.scenario = a.scenario and r.user_id = a.user_id and r.window_start = a.window_start
join {{ ref('stg_users') }} u
  on u.scenario = a.scenario and u.user_id = a.user_id
left join {{ ref('int_geo_speed') }} g
  on g.scenario = a.scenario and g.user_id = a.user_id and g.window_start = a.window_start
