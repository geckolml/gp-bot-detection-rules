-- Regla generada automáticamente por evo/export_dbt.py. No editar a mano.
-- corrida: 20261115-055801_multi_p200_g150_cx0.8_m0.3_h8_s42 | regla: rule_24 | nodos: 15
-- entrenamiento: TPR=0.9877 FPR=0.0195
-- prueba:        TPR=0.8543 FPR=0.0162
-- legible: ((account_age_hours < 530.2) AND ((link_ratio > 0) OR (avg_msg_len > 30.35))) AND (reply_rate < 0.3333)
select
    scenario,
    user_id,
    window_start,
    'flag_bots_rule_24' as rule_id
from {{ ref('fct_user_activity_hourly') }}
where ((account_age_hours < 530.2285111111114e0) AND ((link_ratio > 0.0) OR (avg_msg_len > 30.35424242424244e0))) AND (reply_rate < 0.3333333333333333e0)
