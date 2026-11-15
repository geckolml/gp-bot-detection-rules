## Why

El enunciado exige entregar el código en un repositorio funcional y reproducible.
Todo el proyecto debe poder ejecutarse con un solo comando, sin instalar
dependencias en la máquina del evaluador, y sin depender de servicios en la nube.

Fase del curso: transversal (soporta las fases II, III y IV).

## What Changes

- Estructura de carpetas del repositorio (`simulator/`, `dbt_project/`, `evo/`,
  `baselines/`, `experiments/`, `notebooks/`, `tests/`, `data/`, `results/`).
- Imagen Docker única con todas las dependencias de Python y dbt.
- `docker-compose.yml` con un servicio por etapa del pipeline y un volumen
  compartido para `data/` y `results/`.
- `Makefile` con atajos para cada etapa.
- Configuración de `pytest` y `.gitignore`.

## Capabilities

### New Capabilities
- `project-infrastructure`: ejecución reproducible del pipeline completo en contenedores.

### Modified Capabilities
- Ninguna.

## Impact

- Archivos nuevos en la raíz: `Dockerfile`, `docker-compose.yml`, `Makefile`,
  `requirements.txt`, `pyproject.toml`, `.gitignore`, `.dockerignore`.
- No hay dependencia de Snowflake: el warehouse es un archivo DuckDB local.
