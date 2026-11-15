"""Estudios de varias corridas: sensibilidad de parámetros y ablación de operadores.

    python -m evo.sensitivity --config experiments/sensitivity.yaml
    python -m evo.sensitivity --config experiments/ablation.yaml
"""
from __future__ import annotations

import argparse
import copy
import itertools
import json
from pathlib import Path

import pandas as pd
import yaml

from evo.config import get_by_path, load_config, set_by_path


def expand_design(base: dict, parameters: dict, design: str = "one_at_a_time") -> list[dict]:
    """Devuelve combinaciones {parámetro: valor}. En 'one_at_a_time' la base aparece una sola vez."""
    if design == "full":
        keys = list(parameters)
        return [dict(zip(keys, vals)) for vals in itertools.product(*parameters.values())]
    base_combo = {k: get_by_path(base, k) for k in parameters}
    for k, vals in parameters.items():
        if base_combo[k] not in vals:
            raise ValueError(f"El valor base de {k} ({base_combo[k]}) no está en {vals}")
    combos = [base_combo]
    for k, vals in parameters.items():
        for v in vals:
            if v != base_combo[k]:
                combos.append({**base_combo, k: v})
    return combos


def combo_label(combo: dict) -> str:
    return "_".join(f"{k.split('.')[-1]}{v}" for k, v in combo.items())


METRICS = ("seed", "hypervolume_final", "best_test_tpr_feasible", "tpr_final_test", "size_final", "runtime_s")


def aggregate(run_dirs: list[Path], fpr_max: float, max_size: int | None = None) -> pd.DataFrame:
    """Una fila por combinación. La regla final de cada corrida se elige aquí
    (solo con entrenamiento) desde pareto.json, con el mismo criterio para todas."""
    from evo.run import select_final_rule

    rows = []
    for d in run_dirs:
        s = json.loads((d / "summary.json").read_text())
        combo = json.loads((d / "combo.json").read_text())
        final = select_final_rule(json.loads((d / "pareto.json").read_text()), fpr_max, max_size)
        rows.append({**combo, "seed": s["seed"], "hypervolume_final": s["hypervolume_final"],
                     "best_test_tpr_feasible": s["best_test_tpr_feasible"],
                     "tpr_final_test": final["test"]["tpr"] if final and "test" in final else None,
                     "size_final": final["size_simplified"] if final else None,
                     "runtime_s": s["runtime_s"]})
    df = pd.DataFrame(rows)
    keys = [c for c in df.columns if c not in METRICS]
    agg = df.groupby(keys, dropna=False).agg(
        n_runs=("seed", "count"),
        hv_mean=("hypervolume_final", "mean"), hv_std=("hypervolume_final", "std"),
        # TPR en prueba de la regla final (elegida solo con entrenamiento)
        tpr_final_test_mean=("tpr_final_test", "mean"), tpr_final_test_std=("tpr_final_test", "std"),
        size_final_mean=("size_final", "mean"),
        # cota superior: mejor TPR en prueba con FPR <= ε en prueba
        tpr_test_mean=("best_test_tpr_feasible", "mean"), tpr_test_std=("best_test_tpr_feasible", "std"),
        runtime_mean=("runtime_s", "mean"), runtime_std=("runtime_s", "std"),
    ).reset_index()
    return agg


def main() -> None:
    ap = argparse.ArgumentParser(description="Estudio de sensibilidad")
    ap.add_argument("--config", default="experiments/sensitivity.yaml")
    ap.add_argument("--dry-run", action="store_true", help="Solo lista las corridas")
    args = ap.parse_args()

    study = load_config(args.config)
    base = load_config(study["base_config"])
    for k, v in (study.get("overrides") or {}).items():
        set_by_path(base, k, v)
    combos = expand_design(base, study["parameters"], study.get("design", "one_at_a_time"))
    seeds = study["seeds"]
    print(f"{len(combos)} combinaciones x {len(seeds)} semillas = {len(combos) * len(seeds)} corridas")
    if args.dry_run:
        for c in combos:
            print(" ", combo_label(c))
        return

    from evo.data import load_features
    from evo.run import run_experiment
    d = base["data"]
    train = load_features(d["warehouse"], d["train_scenario"], d["table"])
    test = load_features(d["warehouse"], d["test_scenario"], d["table"])

    run_dirs = []
    for combo in combos:
        for seed in seeds:
            cfg = copy.deepcopy(base)
            for k, v in combo.items():
                set_by_path(cfg, k, v)
            cfg["seed"] = seed
            run_id = f"{combo_label(combo)}_s{seed}"
            out = Path(cfg["output_dir"]) / run_id
            if (out / "summary.json").exists():
                print(f"[omitida, ya existe] {run_id}")
            else:
                print(f"[corriendo] {run_id}")
                out = run_experiment(cfg, run_id, train=train, test=test, verbose=False)
            with open(out / "combo.json", "w") as f:
                json.dump(combo, f)
            run_dirs.append(out)

    table = aggregate(run_dirs, base["fitness"]["fpr_max"], (base.get("selection") or {}).get("max_size"))
    out_table = Path(study.get("output_table", "results/tables/sensitivity.csv"))
    out_table.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_table, index=False)
    print(table.to_string(index=False))
    print(f"-> {out_table}")


if __name__ == "__main__":
    main()
