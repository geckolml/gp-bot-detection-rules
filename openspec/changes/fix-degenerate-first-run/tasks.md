## 1. Simulador

- [x] 1.1 Generador de texto con frases comunes compartidas (`simulator/agents.py`), usado también por las respuestas
- [x] 1.2 Parámetros `n_common_phrases` y `common_phrase_prob` por tipo de agente; `legit.geo_jump_prob = 0.01` (`simulator/config.yaml`)
- [x] 1.3 Test: más del 2 % de las ventanas de `legit` tiene mensajes repetidos
- [x] 1.4 Test: un agente con `common_phrase_prob = 0` no usa el vocabulario común

## 2. Evolución

- [x] 2.1 Eliminación de clones por vector de objetivos antes del reemplazo (`evo/algorithms.py`)
- [x] 2.2 Mutación de crecimiento `extend` y nuevos pesos de mutación (`experiments/base.yaml`)
- [x] 2.3 Punto de referencia fijo `fitness.hv_ref_size` para el hipervolumen
- [x] 2.4 Test de población sin clones (más y menos vectores distintos que μ)
- [x] 2.5 Test de la mutación de crecimiento (árbol válido, regla original conservada)
- [x] 2.6 Test de hipervolumen independiente de `max_height`

## 3. Reporte

- [x] 3.1 Corrida principal = la más reciente fuera de subcarpetas (`evo/report.py`)
- [x] 3.2 Test de selección de la corrida principal

## 4. Verificación

- [x] 4.1 Regenerar datos y features (`make data`, `make features`) y comprobar que ninguna comparación de una variable alcanza `FPR = 0` con TPR alto
- [x] 4.2 `make test` y `openspec validate --all`
- [x] 4.3 Repetir `make evolve`, `make baselines`, `make sensitivity` y `make report`; revisar que el hipervolumen crece y que las corridas difieren entre semillas
- [x] 4.4 Actualizar la tabla de parámetros del README
