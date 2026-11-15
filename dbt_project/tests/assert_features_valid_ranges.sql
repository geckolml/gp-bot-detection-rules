-- Proporciones en [0, 1], al menos un mensaje y valores no negativos
select *
from {{ ref('fct_user_activity_hourly') }}
where link_ratio not between 0 and 1
   or dup_template_ratio not between 0 and 1
   or reply_rate not between 0 and 1
   or msgs_count < 1
   or unique_recipients < 1
   or max_geo_speed_kmh < 0
   or account_age_hours < 0
