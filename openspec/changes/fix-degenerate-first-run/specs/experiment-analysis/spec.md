## ADDED Requirements

### Requirement: Corrida principal del reporte
`make report` SHALL usar como corrida principal la más reciente guardada
directamente en `results/runs/`, y no las corridas del estudio de sensibilidad,
salvo que se indique otra con `--run`.

#### Scenario: Reporte después del estudio de sensibilidad
- **WHEN** existe una corrida base y después se ejecuta `make sensitivity`
- **THEN** `make report` usa la corrida base para el frente de Pareto y la tabla de comparación
