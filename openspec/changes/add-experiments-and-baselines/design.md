## Decisions

### Métodos de referencia (mismas métricas TPR / FPR / tamaño)

| Método | Tipo | Tamaño reportado |
|---|---|---|
| Regla manual | heurística de experto (umbrales fijos) | nodos de la regla |
| Árbol de decisión (profundidad 3 y 5) | clásico, interpretable | nodos del árbol |
| Regresión logística (umbral ajustado a `FPR ≤ ε` en entrenamiento) | clásico, no interpretable como regla | número de coeficientes |
| LCS (adaptado del cuaderno de la clase) | evolutivo basado en reglas | condiciones de las reglas que deciden alguna fila |
| PG de un objetivo (modo `single` de `rule-evolution`) | evolutivo, misma representación | nodos de la regla |

El LCS (`baselines/lcs.py`) conserva la mecánica del cuaderno del curso
(modelo de Michigan simplificado: condición ternaria `0/1/#` → acción, actúa la
regla de mayor aptitud que casa, recompensa `+0,1` o penalización `×0,95`,
torneo binario y mutación, sin cruce). Cambios necesarios: las features reales
se convierten en bits comparándolas con cuantiles de entrenamiento (0,1, 0,5 y
0,9: 27 bits); cada generación se evalúa sobre una muestra de 512 filas; la
proporción de comodines es configurable (0,85) y la tasa de mutación por gen
baja de 0,1 a 0,03, porque con 27 bits la del cuaderno destruye las reglas
buenas; una fila sin regla que case se considera usuario real. El LCS no
maneja la restricción `FPR ≤ ε`: se reporta su FPR tal como resulta.

La corrida de un objetivo (`make evolve-single`) se guarda en
`results/runs/single/` y `make report` agrega su regla final a la tabla de
comparación como `gp_single`.

### Estudio de sensibilidad
Grilla en `experiments/sensitivity.yaml` sobre tamaño de población,
probabilidad de cruce, probabilidad de mutación y altura máxima, con 5 semillas
por combinación. Por defecto se varía un parámetro a la vez alrededor de la
configuración base (diseño "uno a la vez"), lo que mantiene el número de
corridas manejable; la grilla completa es opcional.

Métricas por combinación: hipervolumen final (media ± desviación),
mejor TPR con `FPR ≤ ε` en prueba y tiempo de ejecución.

### Figuras
1. Convergencia: mejor y promedio de cada objetivo por generación, con banda de
   ±1 desviación entre semillas.
2. Hipervolumen por generación.
3. Frente de Pareto (TPR vs FPR, tamaño como color) con los métodos base como puntos.
4. Sensibilidad: hipervolumen final por valor de cada parámetro.
5. Comparación entrenamiento vs prueba (bot sigiloso) por método.
