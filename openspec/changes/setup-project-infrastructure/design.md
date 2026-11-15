## Context

El proyecto tiene cuatro etapas encadenadas: simulación → features (dbt) →
evolución (DEAP) → análisis. Cada etapa lee y escribe archivos en un volumen
compartido, así que pueden correrse por separado.

## Goals / Non-Goals

**Goals**
- `docker compose run --rm <servicio>` ejecuta cualquier etapa.
- Una sola imagen para todos los servicios (más simple de construir y mantener).
- Los datos generados nunca se versionan en git.

**Non-Goals**
- Despliegue en la nube o en un warehouse gestionado.
- Orquestación con Airflow/Dagster (innecesario para el alcance del curso).

## Decisions

1. **Imagen base `python:3.11-slim`**: DEAP, DuckDB y dbt-duckdb tienen
   wheels para 3.11. Se evita 3.12+ por compatibilidad de dbt.
2. **Un servicio por etapa** (`sim`, `dbt`, `evo`, `baselines`, `test`,
   `jupyter`) usando la misma imagen y distinto `command`.
3. **Volúmenes**: el repositorio se monta en `/app`, por lo que los cambios de
   código no requieren reconstruir la imagen. `data/` y `results/` quedan en
   el host.
4. **Paralelismo**: la evaluación de la población usa `multiprocessing` con
   método `fork` (Linux dentro del contenedor). Tema de la semana 9 del curso.
5. **Versiones**: `requirements.txt` fija rangos compatibles; tras la primera
   construcción exitosa se congela con `pip freeze > requirements.lock`.

## Risks / Trade-offs

- [Imagen grande por jupyterlab y dbt] → aceptable; se construye una sola vez.
- [Rangos de versiones en lugar de versiones exactas] → mitigado con
  `requirements.lock` tras la primera construcción.
