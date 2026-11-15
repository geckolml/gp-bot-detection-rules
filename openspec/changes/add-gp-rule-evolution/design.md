## Context

Sea `X ∈ R^{n×p}` la matriz de features (filas = usuario × hora, p = 9) y
`y ∈ {0,1}^n` la etiqueta de bot. Una regla es una función booleana
`r: R^p → {0,1}` representada como árbol. Se busca el conjunto de reglas
no dominadas respecto de:

- `f1(r) = TPR(r) = |{i : r(x_i)=1, y_i=1}| / |{i : y_i=1}|` → maximizar (recall de bots)
- `f2(r) = FPR(r) = |{i : r(x_i)=1, y_i=0}| / |{i : y_i=0}|` → minimizar
- `f3(r) = |r|` (número de nodos del árbol) → minimizar (interpretabilidad / control de bloat)

sujeto a `FPR(r) ≤ ε` (por defecto `ε = 0.02`), porque bloquear a usuarios
reales afecta directamente la retención, el DAU/MAU y la carga de soporte.

## Decisions

### Paradigma: Programación Genética tipada (semana 12)
Las reglas tienen estructura variable, por lo que una codificación de longitud
fija (AG canónico) no es natural. La PG tipada garantiza que todo árbol
generado, cruzado o mutado sea sintácticamente válido (una comparación siempre
recibe una feature y un umbral), equivalente a "operadores que respetan
restricciones" (semana 5).

### Conjunto de primitivas

| Nodo | Tipo de entrada | Tipo de salida |
|---|---|---|
| `and_`, `or_` | `bool, bool` | `bool` |
| `not_` | `bool` | `bool` |
| `gt`, `lt` | `Feature, Quantile` | `bool` |
| terminales de feature (9) | — | `Feature` |
| umbral efímero `q ∈ [0.01, 0.99]` | — | `Quantile` |
| `True`, `False` | — | `bool` |

### Umbrales como cuantiles
`gt(f, q)` significa "la feature `f` es mayor que su cuantil `q` en los datos
de entrenamiento". Así un mismo umbral efímero tiene sentido para cualquier
feature (sin importar su escala) y la regla siempre usa valores dentro del
rango observado. Al compilar a SQL, `q` se reemplaza por el valor real del
cuantil (tabla de cuantiles guardada con la corrida).

### Evaluador propio
En lugar de `gp.compile` (que usa `eval`), un intérprete recursivo sobre la
lista prefija del árbol evalúa la regla vectorizada con numpy. El mismo
recorrido sirve al compilador SQL, lo que facilita probar la equivalencia.

### Generación de árboles
Generador propio basado en `gp.generate` de DEAP que fuerza un terminal cuando
el tipo pedido no tiene primitivas (`Feature`, `Quantile`), evitando el error
conocido de DEAP con PG tipada. Inicialización ramped half-and-half
(profundidad 1–4).

### Operadores
- Cruce: intercambio de subárboles de igual tipo. Se usa una versión propia de
  `cxOnePoint` (`cx_one_point`) que elige el tipo de una lista ordenada: la de
  DEAP lo elige de un `set` de clases, cuyo orden depende de direcciones de
  memoria, y con la misma semilla el resultado cambiaba de un proceso a otro.
- Mutación (una al azar): subárbol nuevo (`mutUniform`), reemplazo de nodo
  (`mutNodeReplacement`: and↔or, gt↔lt, cambio de feature) y perturbación del
  umbral (`mutEphemeral`).
- Límite estático de altura (por defecto 8) en cruce y mutación (control de bloat).

### Modos de optimización
- `multi`: NSGA-II (semana 10), esquema (μ+λ), elitista por construcción.
  La restricción se maneja penalizando `f1`: si `FPR > ε`,
  `f1' = TPR − λ·(FPR − ε)` con `λ` configurable (semana 5).
- `single`: `F = TPR − w·FPR − α·|r|` con selección por torneo y elitismo
  (salón de la fama). Sirve como referencia para justificar el multiobjetivo.

### Métricas por generación
Máximo, promedio y mínimo de cada objetivo, número de evaluaciones e
hipervolumen del frente (modo `multi`), con punto de referencia
`(TPR=0, FPR=1, tamaño=tamaño_máximo)`.

### Paralelismo (semana 9)
Evaluación de la población con `multiprocessing.Pool` (modelo maestro-esclavo),
activable desde la configuración.

### Salidas por corrida (`results/runs/<run_id>/`)
`config.yaml`, `quantiles.json`, `logbook.csv`, `pareto.json` (árbol, objetivos
en entrenamiento y en prueba) y `summary.json`.

## Risks / Trade-offs

- [Reglas triviales (`True`) o redundantes (`x AND x`)] → el objetivo de
  tamaño y la penalización de FPR las desplazan; se reporta además la regla
  simplificada.
- [Costo de evaluación con muchos datos] → evaluación vectorizada y
  submuestreo estratificado configurable.
