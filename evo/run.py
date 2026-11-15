"""Ejecuta una corrida de evolución de reglas.

    python -m evo.run --config experiments/base.yaml
    python -m evo.run --config experiments/base.yaml --set algorithm.population=400 --set seed=3
"""
from __future__ import annotations

import argparse
import copy
import json
import multiprocessing as mp
import random
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from evo import fitness
from evo.config import load_config, set_by_path
from evo.data import Dataset, QuantileTable, load_features
from evo.to_sql import to_sql, validate_sql
from evo.tree_eval import evaluate, features_used, simplify, size, to_nested


def make_run_id(cfg: dict) -> str:
    a = cfg["algorithm"]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return (f"{stamp}_{a['mode']}_p{a['population']}_g{a['generations']}_cx{a['cxpb']}"
            f"_m{a['mutpb']}_h{a['max_height']}_s{cfg['seed']}")


def describe_rule(tree: tuple, qtable: QuantileTable, train: Dataset, test: Dataset | None) -> dict:
    tree_s = simplify(tree)
    out = {
        "tree": repr(tree),
        "tree_simplified": repr(tree_s),
        "size": size(tree),
        "size_simplified": size(tree_s),
        "features": sorted(features_used(tree_s)),
        "sql": to_sql(tree_s, qtable),
        "sql_readable": to_sql(tree_s, qtable, readable=True),
    }
    validate_sql(out["sql"])
    out["train"] = fitness.metrics_by_type(evaluate(tree_s, train.X, qtable), train.y, train.agent_type)
    if test is not None:
        out["test"] = fitness.metrics_by_type(evaluate(tree_s, test.X, qtable), test.y, test.agent_type)
    return out


def select_final_rule(rules: list[dict], fpr_max: float, max_size: int | None = None) -> dict | None:
    """Regla final de una corrida: la de mayor TPR en entrenamiento entre las
    que cumplen FPR <= fpr_max en entrenamiento y tienen a lo sumo max_size
    nodos (regla simplificada). Empates: la de menos nodos.

    No usa las métricas de prueba: elegir con ellas filtraría información del
    escenario que mide la generalización.
    """
    feasible = [r for r in rules
                if r["train"]["fpr"] <= fpr_max and (max_size is None or r["size_simplified"] <= max_size)]
    return max(feasible, key=lambda r: (r["train"]["tpr"], -r["size_simplified"])) if feasible else None


def best_on_test(rules: list[dict], fpr_max: float) -> dict | None:
    """Cota superior: mejor TPR en prueba entre las reglas con FPR <= fpr_max
    en prueba. Mira la prueba, así que solo sirve para comparar configuraciones
    (estudio de sensibilidad), nunca para elegir la regla que se reporta."""
    feasible = [r for r in rules if "test" in r and r["test"]["fpr"] <= fpr_max]
    return max(feasible, key=lambda r: (r["test"]["tpr"], -r["size_simplified"])) if feasible else None


def size_tradeoff(rules: list[dict], fpr_max: float, budgets: list[int | None]) -> list[dict]:
    """Costo de la legibilidad: regla final para cada presupuesto de nodos."""
    rows = []
    for budget in budgets:
        r = select_final_rule(rules, fpr_max, budget)
        if r is None:
            continue
        row = {"max_size": budget, "rule_id": r["rule_id"], "size": r["size_simplified"],
               "train_tpr": r["train"]["tpr"], "train_fpr": r["train"]["fpr"]}
        if "test" in r:
            row.update({f"test_{k}": v for k, v in r["test"].items()})
        row["sql_readable"] = r["sql_readable"]
        rows.append(row)
    return rows


def run_experiment(cfg: dict, run_id: str | None = None, train: Dataset | None = None,
                   test: Dataset | None = None, verbose: bool = True) -> Path:
    from evo import algorithms, primitives  # requiere DEAP

    cfg = copy.deepcopy(cfg)
    seed = int(cfg["seed"])
    random.seed(seed)
    np.random.seed(seed)
    alg, fit_cfg, data_cfg = cfg["algorithm"], cfg["fitness"], cfg["data"]
    mode = alg["mode"]

    if train is None:
        train = load_features(data_cfg["warehouse"], data_cfg["train_scenario"], data_cfg["table"])
    if test is None and data_cfg.get("test_scenario"):
        test = load_features(data_cfg["warehouse"], data_cfg["test_scenario"], data_cfg["table"])
    train = train.subsample(data_cfg.get("max_train_rows"), seed)

    qtable = QuantileTable(train.X)
    fitness.init_state(train, qtable, fit_cfg, mode)
    pset = primitives.build_pset()
    tb = algorithms.build_toolbox(pset, alg, mode)

    par = cfg.get("parallel", {})
    pool = None
    mapper = map
    if par.get("enabled"):
        pool = mp.get_context("fork").Pool(par.get("processes"))
        mapper = pool.map

    t0 = time.perf_counter()
    try:
        if mode == "multi":
            pop, front, log = algorithms.run_nsga2(
                tb, alg, mapper, verbose, fit_cfg.get("hv_ref_size", algorithms.DEFAULT_HV_REF_SIZE))
        else:
            pop, front, log = algorithms.run_single(tb, alg, mapper, verbose)
    finally:
        if pool is not None:
            pool.close()
            pool.join()
    runtime = time.perf_counter() - t0

    # Reglas finales (deduplicadas por SQL)
    rules, seen = [], set()
    for ind in front:
        r = describe_rule(to_nested(ind), qtable, train, test)
        if r["sql"] in seen:
            continue
        seen.add(r["sql"])
        r["fitness"] = list(ind.fitness.values)
        rules.append(r)
    rules.sort(key=lambda r: (-r["train"]["tpr"], r["train"]["fpr"], r["size_simplified"]))
    for i, r in enumerate(rules):
        r["rule_id"] = f"rule_{i:02d}"

    run_id = run_id or make_run_id(cfg)
    out = Path(cfg.get("output_dir", "results/runs")) / run_id
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "config.yaml", "w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)
    pd.DataFrame(log).to_csv(out / "logbook.csv", index=False)
    with open(out / "quantiles.json", "w") as f:
        json.dump(qtable.grid(), f)
    with open(out / "pareto.json", "w") as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)

    best = select_final_rule(rules, fit_cfg["fpr_max"], (cfg.get("selection") or {}).get("max_size"))
    oracle = best_on_test(rules, fit_cfg["fpr_max"])
    has_test = bool(best) and "test" in best
    summary = {
        "run_id": run_id,
        "mode": mode,
        "seed": seed,
        "params": {k: alg[k] for k in ("population", "generations", "cxpb", "mutpb", "max_height")},
        "runtime_s": round(runtime, 2),
        "n_train_rows": train.n,
        "n_rules": len(rules),
        "hypervolume_final": log[-1].get("hypervolume"),
        # Regla final: elegida solo con entrenamiento (ver select_final_rule)
        "best_rule_id": best["rule_id"] if best else None,
        "best_size": best["size_simplified"] if best else None,
        "best_train_tpr": best["train"]["tpr"] if best else None,
        "best_train_fpr": best["train"]["fpr"] if best else None,
        "best_test_tpr": best["test"]["tpr"] if has_test else None,
        "best_test_fpr": best["test"]["fpr"] if has_test else None,
        "best_sql_readable": best["sql_readable"] if best else None,
        # Cota superior mirando la prueba (solo para comparar configuraciones)
        "best_test_tpr_feasible": oracle["test"]["tpr"] if oracle else None,
    }
    with open(out / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    if verbose:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        print(f"Resultados en {out}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Evolución de reglas de detección de bots (PG + NSGA-II)")
    ap.add_argument("--config", default="experiments/base.yaml")
    ap.add_argument("--set", action="append", default=[], metavar="clave=valor",
                    help="Sobrescribe un parámetro, p. ej. --set algorithm.population=400")
    ap.add_argument("--run-id", default=None)
    args = ap.parse_args()
    cfg = load_config(args.config)
    for item in args.set:
        k, v = item.split("=", 1)
        set_by_path(cfg, k, yaml.safe_load(v))
    run_experiment(cfg, args.run_id)


if __name__ == "__main__":
    main()
