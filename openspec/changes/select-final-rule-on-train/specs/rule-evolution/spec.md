## ADDED Requirements

### Requirement: Selección de la regla final
El sistema SHALL elegir la regla final de una corrida como la de mayor TPR en
entrenamiento entre las reglas del frente que cumplen `FPR ≤ ε` en
entrenamiento y tienen a lo sumo `selection.max_size` nodos una vez
simplificadas; en caso de empate, la de menos nodos. Las métricas del
escenario de prueba MUST NOT intervenir en la elección.

#### Scenario: La prueba no interviene
- **WHEN** dos reglas cumplen la restricción en entrenamiento y la de menor TPR en entrenamiento tiene mayor TPR en prueba
- **THEN** se elige la de mayor TPR en entrenamiento

#### Scenario: Presupuesto de tamaño
- **WHEN** `selection.max_size` es 15 y la regla de mayor TPR en entrenamiento tiene 40 nodos
- **THEN** se elige la mejor regla de 15 nodos o menos

#### Scenario: Sin regla factible
- **WHEN** ninguna regla del frente cumple `FPR ≤ ε` en entrenamiento dentro del presupuesto de tamaño
- **THEN** la corrida no tiene regla final y `best_rule_id` queda vacío

#### Scenario: Métricas reportadas
- **WHEN** termina una corrida con regla final
- **THEN** `summary.json` incluye su TPR y FPR en entrenamiento y en prueba y su número de nodos
