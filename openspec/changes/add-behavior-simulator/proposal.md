## Why

El enunciado pide indicar el "modelo del proceso a optimizar". No se usarán
datos reales de usuarios por privacidad, así que el proceso se modela con un
simulador propio basado en agentes que genera la actividad de la plataforma
(mensajes y ubicaciones) con etiquetas conocidas (usuario real o bot).

Fase del curso: I (Definición y modelado del problema).

## What Changes

- Simulador basado en agentes en `simulator/` con cuatro tipos de agente:
  usuario real, bot ingenuo, bot adaptativo y bot sigiloso.
- Escenarios configurables en YAML (`train` y `test`): el escenario `test`
  incluye el bot sigiloso, que nunca aparece en entrenamiento, para medir
  generalización.
- Salida en Parquet: tablas `users`, `messages` y `locations`.

## Capabilities

### New Capabilities
- `behavior-simulator`: generación reproducible de actividad sintética etiquetada.

### Modified Capabilities
- Ninguna.

## Impact

- Código nuevo: `simulator/agents.py`, `simulator/simulate.py`, `simulator/config.yaml`.
- Datos en `data/raw/<escenario>/` (no versionados).
- Es la entrada de `feature-pipeline`.
