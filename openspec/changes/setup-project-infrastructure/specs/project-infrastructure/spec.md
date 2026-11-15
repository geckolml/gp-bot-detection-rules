## ADDED Requirements

### Requirement: Ejecución en contenedores
El proyecto SHALL ejecutar cada etapa del pipeline (simulación, features,
evolución, métodos base, tests y análisis) dentro de un contenedor Docker
definido en `docker-compose.yml`, sin requerir dependencias de Python en el host.

#### Scenario: Ejecutar una etapa
- **WHEN** el usuario ejecuta `docker compose run --rm sim`
- **THEN** el simulador corre dentro del contenedor y escribe sus salidas en `data/raw/` del host

#### Scenario: Pipeline completo
- **WHEN** el usuario ejecuta `make all`
- **THEN** se ejecutan en orden simulación, features, evolución y métodos base sin intervención manual

### Requirement: Datos fuera del control de versiones
El repositorio MUST excluir de git los datos generados, la base DuckDB, los
artefactos de dbt y las corridas de experimentos.

#### Scenario: Archivos generados ignorados
- **WHEN** se ejecuta el pipeline completo y luego `git status`
- **THEN** no aparecen archivos de `data/`, `results/runs/`, `*.duckdb` ni `dbt_project/target/`

### Requirement: Tests automatizados
El proyecto SHALL tener una suite de `pytest` ejecutable con `make test`.
Los tests que dependan de librerías opcionales MUST omitirse (skip) en lugar de
fallar cuando la librería no esté instalada.

#### Scenario: Correr la suite en el contenedor
- **WHEN** el usuario ejecuta `make test`
- **THEN** pytest corre dentro del contenedor y reporta el resultado de todos los tests
