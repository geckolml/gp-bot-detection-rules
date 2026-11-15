## ADDED Requirements

### Requirement: Árboles tipados válidos
El sistema SHALL representar cada regla como un árbol de Programación Genética
tipada cuya raíz devuelve `bool`, donde toda comparación (`gt`, `lt`) recibe
exactamente una feature y un umbral de cuantil. La inicialización, el cruce y
la mutación MUST producir siempre árboles válidos bajo estas reglas de tipo.

#### Scenario: Población inicial válida
- **WHEN** se inicializa una población de 200 individuos
- **THEN** todos los árboles tienen raíz de tipo `bool` y todas las comparaciones reciben una feature y un cuantil

#### Scenario: Descendencia válida
- **WHEN** se aplican cruce y mutación durante 10 generaciones
- **THEN** ningún individuo viola las reglas de tipo ni supera la altura máxima configurada

### Requirement: Evaluación vectorizada de reglas
El sistema SHALL evaluar una regla sobre la matriz de features devolviendo una
máscara booleana por fila, donde `gt(f, q)` es verdadero si el valor de `f`
supera el cuantil `q` de `f` en los datos de entrenamiento.

#### Scenario: Comparación con cuantil
- **WHEN** se evalúa `gt(msgs_per_min, 0.9)`
- **THEN** la máscara es verdadera exactamente en las filas cuyo `msgs_per_min` supera el percentil 90 de entrenamiento

### Requirement: Objetivos de aptitud
En modo `multi` el sistema SHALL calcular para cada individuo
`(TPR, FPR, tamaño)` maximizando el primero y minimizando los otros dos.
En modo `single` SHALL calcular `TPR − w·FPR − α·tamaño`.

#### Scenario: Regla que marca todo
- **WHEN** se evalúa la regla `True`
- **THEN** sus objetivos sin penalización son `TPR = 1`, `FPR = 1` y `tamaño = 1`

### Requirement: Restricción de falsos positivos
Cuando `FPR > ε`, el sistema MUST penalizar el objetivo de detección según
`TPR − λ·(FPR − ε)`. Cuando `FPR ≤ ε` no MUST aplicar penalización.

#### Scenario: Regla que viola la restricción
- **WHEN** una regla tiene `TPR = 0.9`, `FPR = 0.12`, `ε = 0.02` y `λ = 5`
- **THEN** su objetivo de detección penalizado es `0.4`

### Requirement: Selección y reemplazo
En modo `multi` el sistema SHALL usar NSGA-II con reemplazo (μ+λ); en modo
`single` SHALL usar selección por torneo con elitismo de al menos un individuo.

#### Scenario: Elitismo en modo single
- **WHEN** se ejecuta el modo `single` por 20 generaciones
- **THEN** la mejor aptitud registrada nunca disminuye entre generaciones

### Requirement: Registro de la evolución
El sistema SHALL registrar por generación el número de evaluaciones, el máximo,
promedio y mínimo de cada objetivo y, en modo `multi`, el hipervolumen del
frente no dominado, y MUST guardarlo en `logbook.csv`.

#### Scenario: Logbook completo
- **WHEN** termina una corrida de 50 generaciones
- **THEN** `logbook.csv` tiene 51 filas (generación 0 a 50)

### Requirement: Reproducibilidad y configuración
Cada corrida SHALL leerse de un archivo YAML, usar una semilla fija y guardar
en `results/runs/<run_id>/` la configuración usada, la tabla de cuantiles, el
logbook, el frente de Pareto (evaluado en entrenamiento y en prueba) y un resumen.

#### Scenario: Misma semilla
- **WHEN** se ejecuta dos veces la misma configuración con la misma semilla y sin paralelismo
- **THEN** los frentes de Pareto resultantes son idénticos

#### Scenario: Evaluación en prueba
- **WHEN** termina una corrida
- **THEN** cada regla de `pareto.json` incluye sus métricas en el escenario `test`
