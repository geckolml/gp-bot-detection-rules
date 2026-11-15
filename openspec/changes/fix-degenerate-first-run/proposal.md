## Why

La primera corrida completa (`make evolve`, tarea 4.6 de `add-gp-rule-evolution`)
terminó sin errores pero con un resultado degenerado: el hipervolumen no cambió
desde la generación 0, el frente tuvo 2 reglas y la mejor fue
`dup_template_ratio > 0` con `FPR = 0`. El estudio de sensibilidad (45 corridas)
devolvió exactamente el mismo resultado en todas. Con esos resultados la fase
IV del enunciado (convergencia, sensibilidad, comparación) no tiene nada que
analizar. Se encontraron cuatro causas:

1. **Datos triviales.** Los usuarios `legit` nunca repiten un mensaje
   (`dup_template_ratio = 0` en el 100 % de sus filas), así que una sola
   comparación detecta el 95,8 % de los bots sin falsos positivos. Esto
   incumple el requisito ya escrito "Señales con solapamiento" de
   `behavior-simulator` (ninguna variable individual separa perfectamente las
   clases); su escenario solo comprobaba el ritmo de mensajes.
2. **Estancamiento del algoritmo.** Los clones de los pocos puntos no dominados
   ocupan las μ plazas de la población y ningún operador agrega una condición
   a una regla que ya funciona, por lo que no aparecen reglas compuestas.
3. **Hipervolumen no comparable.** Su punto de referencia depende de
   `max_height`, uno de los parámetros que varía el estudio de sensibilidad:
   el mismo frente da 0,935, 0,952 o 0,956 según la altura máxima.
4. **Corrida principal del reporte.** Después de `make sensitivity`,
   `make report` toma como corrida principal la última del estudio en lugar de
   la corrida base.

Fase del curso: I (modelado del problema), II (diseño del algoritmo) y IV (análisis).

## What Changes

- Simulador: vocabulario de frases comunes compartido por todos los usuarios
  (los usuarios reales también repiten mensajes) y una probabilidad pequeña de
  salto de ubicación en usuarios reales.
- Evolución: eliminación de clones antes del reemplazo (μ+λ) y nueva mutación
  de crecimiento (`x → and_(x, nuevo)` / `or_(x, nuevo)`).
- Hipervolumen con punto de referencia fijo, independiente de los parámetros.
- Reporte: la corrida principal es la más reciente fuera del estudio de sensibilidad.
- Se regeneran datos, features, corridas, tablas y figuras.

## Capabilities

### New Capabilities
- Ninguna.

### Modified Capabilities
- `behavior-simulator`: mensajes repetidos en todos los tipos de agente.
- `rule-evolution`: población sin clones, mutación de crecimiento e hipervolumen comparable.
- `experiment-analysis`: corrida principal del reporte.

## Impact

- Código: `simulator/agents.py`, `simulator/config.yaml`, `evo/algorithms.py`,
  `evo/report.py`, `experiments/base.yaml`, tests.
- Los datos sintéticos cambian (misma semilla, distinto resultado que antes del cambio).
- Todas las corridas y figuras anteriores quedan obsoletas y se regeneran.
