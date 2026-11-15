## ADDED Requirements

### Requirement: Tipos de agente
El simulador SHALL generar usuarios de los tipos `legit`, `naive_bot`,
`adaptive_bot` y `stealth_bot`, con la cantidad de cada tipo definida por
escenario en `simulator/config.yaml`. Todo usuario cuyo tipo termine en `_bot`
MUST tener `is_bot = true`.

#### Scenario: Cantidades por escenario
- **WHEN** el escenario define 1000 `legit` y 100 `naive_bot`
- **THEN** la tabla `users` contiene exactamente 1000 usuarios `legit` y 100 `naive_bot`

#### Scenario: Etiqueta consistente
- **WHEN** se genera cualquier escenario
- **THEN** `is_bot` es verdadero si y solo si `agent_type` termina en `_bot`

### Requirement: Escenario de prueba con bot no visto
El escenario `test` SHALL incluir agentes `stealth_bot` y el escenario `train`
MUST NOT incluirlos.

#### Scenario: Bot sigiloso solo en prueba
- **WHEN** se generan los escenarios `train` y `test` con la configuración por defecto
- **THEN** `stealth_bot` aparece en `test` y no aparece en `train`

### Requirement: Reproducibilidad
El simulador SHALL producir resultados idénticos para la misma configuración y semilla.

#### Scenario: Misma semilla
- **WHEN** se ejecuta dos veces el escenario `train` con la semilla 42
- **THEN** las tres tablas generadas son idénticas

### Requirement: Integridad de los datos
Los mensajes MUST tener remitente y destinatario existentes en `users`, distintos
entre sí, y con `sent_at` posterior o igual al `created_at` del remitente.

#### Scenario: Integridad referencial
- **WHEN** se genera un escenario
- **THEN** todo `sender_id` y `recipient_id` existe en `users` y `sender_id != recipient_id`

#### Scenario: Orden temporal
- **WHEN** se genera un escenario
- **THEN** ningún mensaje tiene `sent_at` anterior al `created_at` de su remitente

### Requirement: Señales con solapamiento
Las distribuciones de comportamiento de `adaptive_bot` y `stealth_bot` SHALL
solaparse con las de `legit` en al menos una variable de ritmo de mensajes, de
modo que ninguna variable individual separe perfectamente las clases.

#### Scenario: Ritmo de mensajes solapado
- **WHEN** se compara el número de mensajes por usuario de `adaptive_bot` y `legit`
- **THEN** el rango intercuartílico de ambos tipos se intersecta

### Requirement: Salida en Parquet
El simulador SHALL escribir `users.parquet`, `messages.parquet` y
`locations.parquet` en `data/raw/<escenario>/`.

#### Scenario: Archivos generados
- **WHEN** el usuario ejecuta `make data`
- **THEN** existen los tres archivos Parquet para los escenarios `train` y `test`
