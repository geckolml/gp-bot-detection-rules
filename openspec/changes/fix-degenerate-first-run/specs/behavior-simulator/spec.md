## ADDED Requirements

### Requirement: Mensajes repetidos en todos los tipos de agente
El simulador SHALL incluir un vocabulario de frases comunes compartido por
todos los usuarios, y cada tipo de agente MUST tener un parámetro
`common_phrase_prob` con la proporción de sus mensajes que son frases comunes,
de modo que los usuarios `legit` también repitan mensajes.

#### Scenario: Usuarios reales con mensajes repetidos
- **WHEN** se genera el escenario `train` con la configuración por defecto
- **THEN** más del 2 % de las ventanas (usuario, hora) de usuarios `legit` contiene al menos un mensaje repetido

#### Scenario: Sin frases comunes
- **WHEN** un tipo de agente tiene `common_phrase_prob = 0`
- **THEN** ninguno de sus mensajes usa un `template_id` del vocabulario común
