## 1. Representación

- [x] 1.1 Definir tipos `Feature` y `Quantile` y el conjunto de primitivas tipado (`evo/primitives.py`)
- [x] 1.2 Generador de árboles que fuerza terminal en tipos sin primitivas (full / grow / half-and-half)
- [x] 1.3 Intérprete vectorizado sobre la lista prefija del árbol (`evo/tree_eval.py`)
- [x] 1.4 Tabla de cuantiles por feature calculada en entrenamiento

## 2. Aptitud

- [x] 2.1 Métricas TPR, FPR y tamaño (`evo/fitness.py`)
- [x] 2.2 Penalización por violar `FPR ≤ ε`
- [x] 2.3 Aptitud escalar del modo `single`

## 3. Algoritmo

- [x] 3.1 Toolbox de DEAP: inicialización, cruce, mutación compuesta y límite de altura (`evo/algorithms.py`)
- [x] 3.2 Bucle NSGA-II (μ+λ) con logbook e hipervolumen
- [x] 3.3 Bucle de un objetivo con torneo y elitismo
- [x] 3.4 Evaluación paralela opcional con `multiprocessing`
- [x] 3.5 CLI `python -m evo.run --config experiments/base.yaml` y guardado de resultados
- [x] 3.6 Cruce de un punto propio (`cx_one_point`): el de DEAP elige el tipo desde un `set` y no es reproducible entre procesos

## 4. Tests

- [x] 4.1 Test del intérprete con árboles conocidos (sin DEAP)
- [x] 4.2 Test de objetivos y penalización
- [x] 4.3 Test de validez de tipos en población y descendencia (requiere DEAP)
- [x] 4.4 Test de reproducibilidad con semilla y de elitismo (requiere DEAP)
- [x] 4.7 Test de reproducibilidad entre procesos separados
- [x] 4.5 Ejecutar todos los tests dentro del contenedor
- [x] 4.6 Primera corrida completa con `make evolve` y revisión de las curvas
