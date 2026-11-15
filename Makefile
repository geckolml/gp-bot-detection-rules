RUN = docker compose run --rm
CONFIG ?= experiments/base.yaml
RUN_ID ?=

.PHONY: build data features evolve evolve-single sensitivity ablation baselines export report test all analysis notebook help

build:            ## Construye la imagen Docker
	docker compose build

data:             ## Genera los datos sintéticos (train y test)
	$(RUN) sim

features:         ## Calcula features con dbt sobre DuckDB y corre los tests de dbt
	$(RUN) dbt

evolve:           ## Una corrida de evolución con la configuración CONFIG
	$(RUN) evo python -m evo.run --config $(CONFIG)

evolve-single:    ## Corrida de un objetivo (referencia para justificar el multiobjetivo)
	$(RUN) evo python -m evo.run --config $(CONFIG) --set algorithm.mode=single --set output_dir=results/runs/single

sensitivity:      ## Estudio de sensibilidad (varias corridas)
	$(RUN) evo python -m evo.sensitivity --config experiments/sensitivity.yaml

ablation:         ## Ablación: con y sin eliminación de clones y mutación de crecimiento
	$(RUN) evo python -m evo.sensitivity --config experiments/ablation.yaml

baselines:        ## Métodos de referencia
	$(RUN) baselines

export:           ## Exporta las reglas de una corrida a modelos dbt (make export RUN_ID=...)
	$(RUN) evo python -m evo.export_dbt --run results/runs/$(RUN_ID)
	$(RUN) dbt dbt run --select path:models/moderation

report:           ## Tablas y figuras para el informe
	$(RUN) evo python -m evo.report

test:             ## Suite de tests
	$(RUN) test

all: data features evolve evolve-single baselines report

analysis:         ## Ejecuta notebooks/01_analisis.ipynb y guarda sus salidas
	$(RUN) evo jupyter nbconvert --to notebook --execute --inplace notebooks/01_analisis.ipynb

notebook:         ## JupyterLab en http://localhost:8888
	docker compose up jupyter

help:
	@grep -E '^[a-z-]+:.*##' Makefile | sed 's/:.*##/\t/'
