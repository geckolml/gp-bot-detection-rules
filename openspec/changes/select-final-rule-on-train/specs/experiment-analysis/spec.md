## ADDED Requirements

### Requirement: Métrica de la regla final en la sensibilidad
La tabla de sensibilidad SHALL incluir, por combinación de parámetros, la media
y la desviación del TPR en prueba de la regla final de cada corrida (elegida
solo con entrenamiento).

#### Scenario: Columnas de la regla final
- **WHEN** terminan las corridas del estudio
- **THEN** `sensitivity.csv` tiene las columnas `tpr_final_test_mean` y `tpr_final_test_std`
