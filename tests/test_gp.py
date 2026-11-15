"""Spec: rule-evolution (requiere DEAP)."""
import random
from functools import partial
from inspect import isclass

import numpy as np
import pytest

pytest.importorskip("deap")
from deap import creator  # noqa: E402

from evo import algorithms, fitness, primitives  # noqa: E402
from evo.data import QuantileTable  # noqa: E402
from evo.tree_eval import to_nested  # noqa: E402
from tests.helpers import synthetic_dataset  # noqa: E402

ALG = {"population": 40, "generations": 10, "cxpb": 0.8, "mutpb": 0.3, "max_height": 6,
       "init_min_depth": 1, "init_max_depth": 4, "tournament_size": 3, "elite": 2}
FIT = {"fpr_max": 0.02, "penalty_lambda": 5.0, "single_fpr_weight": 5.0, "parsimony": 0.002}


def setup(mode: str, seed: int = 0, alg: dict = ALG):
    random.seed(seed)
    np.random.seed(seed)
    ds = synthetic_dataset(n=1500, seed=seed)
    fitness.init_state(ds, QuantileTable(ds.X), FIT, mode)
    pset = primitives.build_pset()
    return algorithms.build_toolbox(pset, alg, mode)


def with_fitness(tb, values: list[tuple]) -> list:
    """Individuos cualesquiera con vectores de objetivos asignados a mano."""
    inds = tb.population(n=len(values))
    for ind, v in zip(inds, values):
        ind.fitness.values = v
    return inds


def test_initial_population_valid():
    tb = setup("multi")
    pop = tb.population(n=200)
    assert all(primitives.is_valid(ind) for ind in pop)
    for ind in pop:
        to_nested(ind)  # no debe fallar


def test_offspring_valid_and_height_limited():
    tb = setup("multi")
    pop, front, log = algorithms.run_nsga2(tb, ALG, verbose=False)
    assert all(primitives.is_valid(ind) for ind in pop)
    assert all(ind.height <= ALG["max_height"] for ind in pop)
    assert len(log) == ALG["generations"] + 1
    assert "hypervolume" in log[-1]


def test_reproducible_front():
    def fronts():
        tb = setup("multi", seed=5)
        _, front, _ = algorithms.run_nsga2(tb, ALG, verbose=False)
        return sorted(str(ind) for ind in front)
    assert fronts() == fronts()


def test_single_mode_elitism():
    tb = setup("single")
    _, _, log = algorithms.run_single(tb, {**ALG, "generations": 20}, verbose=False)
    best = [row["fitness_max"] for row in log]
    assert all(b2 >= b1 - 1e-12 for b1, b2 in zip(best, best[1:]))


def test_survivors_distinct_when_more_unique_vectors_than_mu():
    tb = setup("multi")
    distinct = [(i / 250, (i * 7 % 250) / 250, 3.0 + i % 5) for i in range(250)]
    pool = with_fitness(tb, distinct + distinct[:150])        # 400 individuos, 250 vectores distintos
    out = algorithms.survivors(pool, 200, tb.select)
    assert len(out) == 200
    assert len({ind.fitness.values for ind in out}) == 200


def test_survivors_filled_with_clones_when_fewer_unique_vectors_than_mu():
    tb = setup("multi")
    distinct = [(i / 50, (i * 7 % 50) / 50, 3.0) for i in range(50)]
    pool = with_fitness(tb, distinct * 8)                     # 400 individuos, 50 vectores distintos
    out = algorithms.survivors(pool, 200, tb.select)
    assert len(out) == 200
    assert {ind.fitness.values for ind in out} == set(distinct)


def test_mut_extend_keeps_original_rule():
    random.seed(3)
    pset = primitives.build_pset()
    q = next(t for t in pset.terminals[primitives.Quantile] if isclass(t))()
    q.value = 0.8
    original = [pset.mapping["gt"], pset.mapping["link_ratio"], q]
    expr = partial(primitives.gen_grow, min_=1, max_=2)
    roots = set()
    for _ in range(50):
        ind, = algorithms.mut_extend(creator.RuleMulti(original), pset, expr)
        assert primitives.is_valid(ind)
        tree = to_nested(ind)
        roots.add(tree[0])
        assert ("gt", ("feat", "link_ratio"), ("q", 0.8)) in tree[1:]
    assert roots == {"and_", "or_"}


def test_hypervolume_does_not_depend_on_max_height():
    for height in (6, 10):
        alg = {**ALG, "max_height": height}
        tb = setup("multi", alg=alg)
        _, front, log = algorithms.run_nsga2(tb, alg, verbose=False)
        fixed = algorithms.hypervolume(front, algorithms.DEFAULT_HV_REF_SIZE)
        assert log[-1]["hypervolume"] == pytest.approx(fixed)
    # mismo frente y misma referencia -> mismo valor, sea cual sea la altura máxima
    assert algorithms.hypervolume(front, 511) != algorithms.hypervolume(front, algorithms.max_nodes(6))


def test_run_experiment_writes_outputs_and_final_rule(tmp_path):
    """Specs: Registro de la evolución, Reproducibilidad y Selección de la regla final."""
    import json

    import pandas as pd

    from evo.run import run_experiment

    ds, ds_test = synthetic_dataset(n=1500, seed=1), synthetic_dataset(n=800, seed=2)
    cfg = {"seed": 7, "output_dir": str(tmp_path), "data": {}, "parallel": {"enabled": False},
           "algorithm": {**ALG, "mode": "multi", "generations": 8},
           "fitness": FIT, "selection": {"max_size": 7}}
    out = run_experiment(cfg, "corrida", train=ds, test=ds_test, verbose=False)
    for name in ("config.yaml", "quantiles.json", "logbook.csv", "pareto.json", "summary.json"):
        assert (out / name).exists()
    assert len(pd.read_csv(out / "logbook.csv")) == 8 + 1
    rules = json.loads((out / "pareto.json").read_text())
    assert all("train" in r and "test" in r for r in rules)
    summary = json.loads((out / "summary.json").read_text())
    final = next(r for r in rules if r["rule_id"] == summary["best_rule_id"])
    assert summary["best_size"] == final["size_simplified"] <= 7
    assert summary["best_train_fpr"] == final["train"]["fpr"] <= FIT["fpr_max"]
    assert summary["best_train_tpr"] == final["train"]["tpr"]
    assert summary["best_test_tpr"] == final["test"]["tpr"]
    assert summary["best_test_fpr"] == final["test"]["fpr"]
    # ninguna regla factible y dentro del presupuesto tiene más TPR en entrenamiento
    feasible = [r for r in rules if r["train"]["fpr"] <= FIT["fpr_max"] and r["size_simplified"] <= 7]
    assert final["train"]["tpr"] == max(r["train"]["tpr"] for r in feasible)


REPRO_SCRIPT = """
import sys
junk = [object() for _ in range(int(sys.argv[1]))]   # cambia la disposición de la memoria
import random
import numpy as np
from evo import algorithms, fitness, primitives
from evo.data import QuantileTable
from tests.helpers import synthetic_dataset
alg = {"population": 40, "generations": 12, "cxpb": 0.8, "mutpb": 0.3, "max_height": 6,
       "init_min_depth": 1, "init_max_depth": 4}
fit = {"fpr_max": 0.02, "penalty_lambda": 5.0}
random.seed(5); np.random.seed(5)
ds = synthetic_dataset(n=1500, seed=5)
fitness.init_state(ds, QuantileTable(ds.X), fit, "multi")
tb = algorithms.build_toolbox(primitives.build_pset(), alg, "multi")
pop, front, log = algorithms.run_nsga2(tb, alg, verbose=False)
print(sorted(str(ind) for ind in pop))
"""


def test_reproducible_across_processes():
    """Spec: Reproducibilidad. Dos ejecuciones separadas con la misma semilla
    dan la misma población aunque cambie la disposición de la memoria (el
    orden de un set de clases depende de ella)."""
    import subprocess
    import sys

    outputs = [subprocess.run([sys.executable, "-c", REPRO_SCRIPT, n], capture_output=True, text=True, check=True).stdout
               for n in ("0", "1", "7", "1000", "12345")]
    assert outputs[0].strip() and len(set(outputs)) == 1
