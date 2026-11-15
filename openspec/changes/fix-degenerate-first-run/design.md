## Context

Mediciones sobre la primera corrida (entrenamiento, 43 026 filas usuario × hora):

| Tipo de agente | Filas con `dup_template_ratio = 0` |
|---|---|
| `legit` | 100,00 % |
| `adaptive_bot` | 12,4 % |
| `naive_bot` | 0,3 % |

Mejor comparación de una sola variable con `FPR ≤ 2 %`: `dup_template_ratio > 0`,
TPR = 0,958 y FPR = 0. En la población final de NSGA-II (μ = 200) había 2
vectores de objetivos distintos; el resto eran clones.

## Goals / Non-Goals

**Goals**
- Que ninguna variable por sí sola resuelva el problema, como ya exigía la spec del simulador.
- Que el algoritmo pueda construir reglas compuestas a partir de reglas simples que funcionan.
- Que el hipervolumen sea comparable entre todas las corridas del estudio de sensibilidad.

**Non-Goals**
- Calibrar el simulador con estadísticas reales (sigue siendo la tarea opcional 4.1 de `add-behavior-simulator`).
- Cambiar los objetivos, la restricción o el tratamiento por penalización.

## Decisions

### Frases comunes compartidas (simulador)
En un chat real una parte de los mensajes son saludos y respuestas cortas
("hola", "ok", "jaja") que se repiten entre usuarios y dentro de una misma
hora. Se agrega un vocabulario de `n_common_phrases` frases (por defecto 40)
con popularidad tipo Zipf. Cada mensaje es una frase común con probabilidad
`common_phrase_prob`, parámetro por tipo de agente:

| Agente | `common_phrase_prob` | Motivo |
|---|---|---|
| `legit` | 0,30 | conversación normal |
| `naive_bot` | 0,00 | solo envía sus plantillas |
| `adaptive_bot` | 0,10 | intercala algo de texto corriente |
| `stealth_bot` | 0,30 | imita a un usuario real |

Las frases comunes tienen `template_id` en un rango propio y longitud corta.
Las respuestas de usuarios reales usan el mismo generador de texto.

Alternativa descartada: dar a cada usuario real unas pocas plantillas propias.
Produce repetición, pero no la coincidencia entre usuarios distintos que sí
ocurre con los saludos.

### Saltos de ubicación en usuarios reales
`legit.geo_jump_prob` pasa de 0 a 0,01 (VPN, GPS falso, error del dispositivo),
para que "velocidad imposible" sea una señal de alta precisión pero no perfecta.

### Población sin clones (NSGA-II, semana 10)
NSGA-II mantiene la diversidad con la distancia de crowding, pero esta no
distingue individuos con objetivos idénticos: todos quedan en el primer frente
y llenan las μ plazas. En PG ocurre con facilidad porque árboles distintos
(p. ej. `gt(f, 0.31)` y `gt(f, 0.52)` cuando ambos cuantiles valen 0) dan el
mismo vector de objetivos. Antes del reemplazo (μ+λ) se conserva un individuo
por vector de objetivos; los clones solo se usan para completar la población
si hay menos de μ vectores distintos. Así los individuos dominados pero
distintos sobreviven y sirven de material para el cruce.

Alternativa descartada: eliminar duplicados por genotipo (texto del árbol). No
resuelve el caso anterior, donde los genotipos difieren.

El parámetro `algorithm.dedupe` (por defecto `true`) existe solo para poder
reproducir la comparación con el algoritmo original; el registro por
generación incluye `n_unique`, el número de vectores de objetivos distintos en
la población.

### Mutación de crecimiento
Operador `extend`: elige un subárbol booleano `x` y lo reemplaza por
`and_(x, nuevo)` u `or_(x, nuevo)`, con `nuevo` generado por `grow`
(profundidad 1–2) y el orden de los hijos al azar. Es el único operador que
agrega una condición conservando la regla existente: `mutUniform` reemplaza el
subárbol y `mutInsert` de DEAP completa los argumentos nuevos solo con
terminales, que para el tipo `bool` son las constantes `True` y `False`.

Pesos de la mutación compuesta: subárbol 0,30, nodo 0,20, umbral 0,25,
crecimiento 0,25. El límite estático de altura sigue controlando el bloat.

### Evidencia (prototipo, 5 semillas, datos con frases comunes)

| Variante | Hipervolumen final | Vectores distintos en la población | TPR entrenamiento (`FPR ≤ 2 %`) | TPR prueba | TPR bot sigiloso |
|---|---|---|---|---|---|
| Algoritmo original | 0,892 | 22 | 0,886 | 0,716 | 0,13 |
| Sin clones | 0,955 | 200 | 0,960 | 0,811 | 0,30 |
| Sin clones + crecimiento | 0,972 | 200 | 0,978 | 0,856 | 0,46 |
| Solo crecimiento | 0,965 | 75 | 0,971 | 0,847 | 0,46 |

Con el algoritmo original, en 4 de 5 semillas la mejor regla factible es una
sola comparación. Con los datos nuevos la mejor comparación de una variable
alcanza TPR = 0,877 (`dup_template_ratio > 0,2`, FPR = 1,5 %).

Resultado final con la configuración definitiva (`make ablation`, 150
generaciones, 5 semillas, regla final elegida solo con entrenamiento):

| Variante | Hipervolumen final | TPR prueba de la regla final |
|---|---|---|
| Con clones, sin crecimiento (diseño inicial) | 0,880 ± 0,002 | 0,697 |
| Con clones, con crecimiento | 0,983 ± 0,001 | 0,845 |
| Sin clones, sin crecimiento | 0,985 ± 0,001 | 0,839 |
| Sin clones, con crecimiento | 0,985 ± 0,001 | 0,848 |

Cualquiera de los dos mecanismos evita el estancamiento; la diferencia entre
las tres variantes corregidas es del orden de la variación entre semillas. Se
conservan los dos: cubren causas distintas (falta de plazas para individuos
intermedios y falta de un operador que haga crecer la regla).

### Punto de referencia fijo del hipervolumen
El tamaño se normaliza con `fitness.hv_ref_size` (por defecto 511, el tamaño
máximo de un árbol binario de altura 8, la altura base) en lugar de
`2^(max_height+1) − 1`. El punto de referencia sigue siendo
`(TPR = 0, FPR = 1, tamaño = hv_ref_size)` y las reglas con más nodos que la
referencia no aportan volumen.

### Corrida principal del reporte
`evo.report` elige la corrida más reciente guardada directamente en
`results/runs/`; las subcarpetas (p. ej. `sensitivity/`) solo se usan si no hay
otra. Las corridas del estudio con la misma configuración que la principal
siguen aportando semillas a las bandas de convergencia.

## Risks / Trade-offs

- [Los parámetros de frases comunes son supuestos, no mediciones] → quedan en
  YAML para calibrarlos con estadísticas agregadas reales.
- [La mutación de crecimiento favorece reglas más grandes] → el objetivo de
  tamaño y el límite de altura lo compensan; se reporta el tamaño de la regla
  simplificada.
- [Eliminar clones cuesta una pasada por la población] → despreciable frente a
  la evaluación.
