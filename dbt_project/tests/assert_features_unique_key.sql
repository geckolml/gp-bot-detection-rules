-- La clave (scenario, user_id, window_start) debe ser única
select scenario, user_id, window_start, count(*) as n
from {{ ref('fct_user_activity_hourly') }}
group by all
having count(*) > 1
