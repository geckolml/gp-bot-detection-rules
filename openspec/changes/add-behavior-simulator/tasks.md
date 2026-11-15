## 1. Configuración

- [x] 1.1 Definir parámetros por tipo de agente y escenarios `train`/`test` en `simulator/config.yaml`

## 2. Implementación

- [x] 2.1 Implementar generación de usuarios y etiquetas (`simulator/agents.py`)
- [x] 2.2 Implementar generación de mensajes por tipo de agente (ritmo, destinatarios, links, plantillas)
- [x] 2.3 Implementar respuestas de usuarios reales con probabilidad según el remitente
- [x] 2.4 Implementar trayectorias de ubicación (realistas vs saltos imposibles)
- [x] 2.5 Implementar CLI `python -m simulator.simulate --scenario train|test|all` con salida Parquet

## 3. Tests

- [x] 3.1 Test de cantidades por tipo y etiqueta consistente
- [x] 3.2 Test de bot sigiloso solo en `test`
- [x] 3.3 Test de reproducibilidad con semilla
- [x] 3.4 Test de integridad referencial y orden temporal
- [x] 3.5 Test de solapamiento del ritmo de mensajes entre `adaptive_bot` y `legit`
- [x] 3.6 Verificar `make data` dentro del contenedor

## 4. Calibración (opcional)

- [ ] 4.1 Ajustar parámetros con estadísticas agregadas (anónimas) de la plataforma real
