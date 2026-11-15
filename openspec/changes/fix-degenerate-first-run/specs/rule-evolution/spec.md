## ADDED Requirements

### Requirement: Población sin clones
En modo `multi`, antes del reemplazo (μ+λ) el sistema SHALL conservar un solo
individuo por cada vector de objetivos distinto. Los individuos repetidos MUST
usarse solo para completar la población cuando hay menos de μ vectores distintos.

#### Scenario: Más vectores distintos que plazas
- **WHEN** padres e hijos suman 400 individuos con 250 vectores de objetivos distintos y μ = 200
- **THEN** los 200 supervivientes tienen vectores de objetivos distintos entre sí

#### Scenario: Menos vectores distintos que plazas
- **WHEN** padres e hijos solo tienen 50 vectores de objetivos distintos y μ = 200
- **THEN** la población resultante tiene 200 individuos e incluye los 50 distintos

### Requirement: Mutación de crecimiento
La mutación SHALL incluir un operador que reemplaza un subárbol booleano `x`
por `and_(x, nuevo)` u `or_(x, nuevo)`, donde `nuevo` es un subárbol aleatorio
válido, conservando `x` sin cambios.

#### Scenario: La regla original se conserva
- **WHEN** se aplica la mutación de crecimiento a `gt(link_ratio, 0.8)`
- **THEN** el resultado es un árbol válido cuya raíz es `and_` u `or_` y uno de sus hijos es `gt(link_ratio, 0.8)`

### Requirement: Hipervolumen comparable entre corridas
El hipervolumen SHALL calcularse con un punto de referencia fijo, tomado de la
configuración (`fitness.hv_ref_size`), que no dependa de los parámetros del
algoritmo.

#### Scenario: Mismo frente con distinta altura máxima
- **WHEN** dos corridas con `max_height` 6 y 10 producen el mismo frente
- **THEN** ambas registran el mismo hipervolumen
