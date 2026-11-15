## ADDED Requirements

### Requirement: Métodos de referencia comparables
El sistema SHALL evaluar una regla manual, un árbol de decisión y una regresión
logística sobre los mismos datos de entrenamiento y prueba que la evolución,
reportando TPR, FPR y tamaño de cada método en ambos escenarios.

#### Scenario: Ejecutar métodos base
- **WHEN** el usuario ejecuta `make baselines`
- **THEN** se escribe `results/tables/baselines.csv` con una fila por método y escenario

### Requirement: Umbral bajo la misma restricción
La regresión logística MUST elegir su umbral de decisión como el que maximiza
TPR sujeto a `FPR ≤ ε` en entrenamiento, para competir bajo la misma
restricción que las reglas evolucionadas.

#### Scenario: Umbral restringido
- **WHEN** se entrena la regresión logística con `ε = 0.02`
- **THEN** su FPR en entrenamiento es menor o igual a 0.02

### Requirement: Árbol de decisión como regla SQL
El árbol de decisión SHALL poder expresarse como una expresión SQL equivalente
(disyunción de las ramas que predicen bot) para comparar su interpretabilidad.

#### Scenario: Exportar árbol
- **WHEN** se entrena un árbol de profundidad 3
- **THEN** se guarda su expresión SQL en `results/tables/baseline_tree_depth3.sql`

### Requirement: Learning Classifier System
El sistema SHALL incluir un LCS adaptado del cuaderno del curso como método de
referencia evolutivo basado en reglas.

#### Scenario: Ejecutar LCS
- **WHEN** el usuario ejecuta `make baselines` con el LCS habilitado
- **THEN** `baselines.csv` incluye filas del método `lcs`
