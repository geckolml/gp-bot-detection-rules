## 1. Estructura y configuración

- [x] 1.1 Crear carpetas `simulator/`, `dbt_project/`, `evo/`, `baselines/`, `experiments/`, `notebooks/`, `tests/`, `data/`, `results/`
- [x] 1.2 Crear `.gitignore` y `.dockerignore` (datos, DuckDB, `target/`, `results/runs/`)
- [x] 1.3 Crear `pyproject.toml` con configuración de pytest (`pythonpath = ["."]`)

## 2. Docker

- [x] 2.1 Escribir `requirements.txt` con rangos de versiones
- [x] 2.2 Escribir `Dockerfile` (python:3.11-slim)
- [x] 2.3 Escribir `docker-compose.yml` con servicios `sim`, `dbt`, `evo`, `baselines`, `test`, `jupyter`
- [x] 2.4 Escribir `Makefile` con objetivos `build`, `data`, `features`, `evolve`, `sensitivity`, `baselines`, `test`, `all`, `notebook`
- [x] 2.5 Construir la imagen (`make build`) y congelar versiones en `requirements.lock`

## 3. Verificación

- [x] 3.1 `make test` pasa dentro del contenedor
- [x] 3.2 `make all` termina sin errores y `git status` no muestra archivos generados
