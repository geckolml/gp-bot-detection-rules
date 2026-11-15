## ADDED Requirements

### Requirement: Estudio de sensibilidad
El sistema SHALL ejecutar el estudio de sensibilidad definido en
`experiments/sensitivity.yaml`, corriendo cada combinación de parámetros con
todas las semillas configuradas y guardando cada corrida en
`results/runs/<run_id>/` con un identificador que incluye los parámetros.

#### Scenario: Diseño uno a la vez
- **WHEN** la configuración varía la población en `[100, 200, 400]` y la mutación en `[0.1, 0.2, 0.4]` con 5 semillas
- **THEN** se ejecutan (3 + 3 − 1) × 5 = 25 corridas, sin repetir la configuración base

### Requirement: Agregación de corridas
El sistema SHALL agregar las corridas en `results/tables/sensitivity.csv` con,
por combinación de parámetros, media y desviación del hipervolumen final, del
mejor TPR en prueba con `FPR ≤ ε` y del tiempo de ejecución.

#### Scenario: Tabla de sensibilidad
- **WHEN** terminan las corridas del estudio
- **THEN** `sensitivity.csv` tiene una fila por combinación con las columnas de media y desviación

### Requirement: Figuras para el informe
El sistema SHALL generar en `results/figures/` las figuras de convergencia,
hipervolumen, frente de Pareto con métodos base, sensibilidad y comparación
entrenamiento vs prueba.

#### Scenario: Generar figuras
- **WHEN** el usuario ejecuta `make report`
- **THEN** existen los archivos PNG de las cinco figuras
