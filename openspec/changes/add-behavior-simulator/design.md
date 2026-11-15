## Context

Se necesitan datos con etiqueta perfecta (bot / no bot) y con dificultad
controlable. Un simulador permite además crear tipos de bot que no se ven en
entrenamiento, que es la forma más honesta de medir si una regla generaliza
(lección tomada de trabajos anteriores del curso, donde el sobreajuste al
periodo de entrenamiento fue el hallazgo central).

## Goals / Non-Goals

**Goals**
- Reproducibilidad total con semilla.
- Distribuciones que se solapan parcialmente entre usuarios reales y bots
  (si las clases fueran separables con una sola variable, el problema sería trivial).
- Parámetros en YAML para poder calibrarlos con estadísticas agregadas reales.

**Non-Goals**
- Contenido real de mensajes (solo metadatos: longitud, plantilla, si tiene link).
- Modelar la red social completa.

## Decisions

### Tipos de agente

| Agente | Ritmo de mensajes | Destinatarios | Links | Plantillas | Geolocalización |
|---|---|---|---|---|---|
| `legit` | bajo, en sesiones | pocos, conversaciones recíprocas | raros | muchas (texto variado) | movimiento realista |
| `naive_bot` | muy alto, constante | muchos, sin respuesta | frecuentes | 1–3 | saltos imposibles |
| `adaptive_bot` | medio, con pausas | moderados | ocasionales | 5–15 | mayormente estable |
| `stealth_bot` (solo `test`) | parecido a `legit` | moderados, pocas respuestas | escasos pero en mensajes cortos | 10–30 | estable |

### Esquema de salida

- `users(user_id, agent_type, is_bot, created_at)`
- `messages(message_id, sender_id, recipient_id, sent_at, has_link, msg_len, template_id)`
- `locations(user_id, recorded_at, lat, lon)`

### Respuestas

Los usuarios reales responden a quien les escribe con una probabilidad que
depende de quién escribe (alta si es otro usuario real, baja si es un bot).
Esto genera la variable "tasa de respuesta recibida", una señal clave.

### Implementación

Simulación vectorizada con numpy por tipo de agente (no un bucle evento a
evento), para generar decenas de miles de usuarios en segundos.

## Risks / Trade-offs

- [Los parámetros del simulador determinan la dificultad del problema] →
  documentar los parámetros en el informe y probar al menos dos niveles de
  dificultad.
- [Sesgo del modelador: reglas que "descubren" lo que se programó] → mitigado
  con el escenario `test` y el bot sigiloso no visto.
