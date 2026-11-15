"""Genera tablas y figuras del informe a partir de las corridas guardadas.

    python -m evo.report                          # corrida más reciente de results/runs/ (sin contar sensitivity/)
    python -m evo.report --run results/runs/<id>  # corrida concreta para el frente de Pareto
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

from evo import plots
from evo.run import size_tradeoff

RUNS = Path("results/runs")
FIG = Path("results/figures")
TAB = Path("results/tables")
SIZE_BUDGETS = [3, 7, 11, 15, 19, 23, 31, None]   # None = sin límite


def _runs(root: Path) -> list[Path]:
    """Corridas terminadas bajo root, de la más antigua a la más reciente."""
    return [p.parent for p in sorted(root.rglob("summary.json"), key=lambda p: p.stat().st_mtime)]


def pick_main_run(root: Path) -> Path | None:
    """Corrida más reciente guardada directamente en root. Las subcarpetas
    (p. ej. sensitivity/) solo se usan si no hay otra."""
    runs = _runs(root)
    top_level = [r for r in runs if r.parent == root]
    candidates = top_level or runs
    return candidates[-1] if candidates else None


def _group_key(run: Path) -> str:
    """Corridas comparables: mismas secciones que afectan a la evolución
    (no la semilla ni las secciones selection, lcs o parallel)."""
    cfg = yaml.safe_load((run / "config.yaml").read_text())
    return json.dumps({k: cfg.get(k) for k in ("algorithm", "fitness", "data")}, sort_keys=True)


def final_rule(run: Path) -> dict | None:
    """Regla final de una corrida (best_rule_id de summary.json)."""
    summary = json.loads((run / "summary.json").read_text())
    rules = json.loads((run / "pareto.json").read_text())
    return next((r for r in rules if r["rule_id"] == summary.get("best_rule_id")), None)


def final_rule_rows(run: Path, method: str) -> list[dict]:
    """Filas (una por escenario) de la regla final, con el formato de baselines.csv."""
    best = final_rule(run)
    if best is None:
        return []
    return [{"method": method, "scenario": s, "size": best["size_simplified"], **best[s]}
            for s in ("train", "test") if s in best]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, default=None)
    args = ap.parse_args()

    runs = _runs(RUNS)
    if not runs:
        raise SystemExit("No hay corridas en results/runs/. Ejecuta make evolve primero.")
    main_run = args.run or pick_main_run(RUNS)
    cfg = yaml.safe_load((main_run / "config.yaml").read_text())

    # Convergencia: todas las corridas con la misma configuración (distintas semillas)
    key = _group_key(main_run)
    by_seed = {}                                  # una corrida por semilla (la más reciente)
    for r in runs:
        if _group_key(r) == key:
            by_seed[yaml.safe_load((r / "config.yaml").read_text())["seed"]] = r
    group = list(by_seed.values())
    logs = [pd.read_csv(r / "logbook.csv") for r in group]
    print(f"Convergencia con {len(group)} corrida(s) de la misma configuración")
    print(" ->", plots.convergence(logs, FIG / "01_convergencia.png"))
    if "hypervolume" in logs[0]:
        print(" ->", plots.hypervolume(logs, FIG / "02_hipervolumen.png"))

    rules = json.loads((main_run / "pareto.json").read_text())
    baselines = pd.read_csv(TAB / "baselines.csv") if (TAB / "baselines.csv").exists() else None
    split = "test" if rules and "test" in rules[0] else "train"
    print(" ->", plots.pareto(rules, baselines, FIG / "03_pareto.png", split, cfg["fitness"]["fpr_max"]))

    if (TAB / "sensitivity.csv").exists():
        sens = pd.read_csv(TAB / "sensitivity.csv")
        print(" ->", plots.sensitivity(sens, FIG / "04_sensibilidad_hv.png"))
        if "tpr_final_test_mean" in sens:     # tablas generadas antes de este cambio no la tienen
            print(" ->", plots.sensitivity(sens, FIG / "04b_sensibilidad_tpr.png", "tpr_final_test",
                                           "TPR en prueba de la regla final"))

    # Comparación final: regla final (elegida solo con entrenamiento) vs métodos base
    rows = final_rule_rows(main_run, "gp_nsga2")
    single = pick_main_run(RUNS / "single")       # corrida de un objetivo, si existe (make evolve-single)
    if single is not None:
        rows += final_rule_rows(single, "gp_single")
    best = final_rule(main_run)
    comp = pd.DataFrame(rows)
    if baselines is not None:
        comp = pd.concat([comp, baselines], ignore_index=True)
    if not comp.empty:
        TAB.mkdir(parents=True, exist_ok=True)
        comp.to_csv(TAB / "comparison.csv", index=False)
        print(comp.round(4).to_string(index=False))
        print(" ->", plots.train_vs_test(comp, FIG / "05_train_vs_test.png"))
    # Costo de la legibilidad: regla final para distintos presupuestos de nodos
    tradeoff = pd.DataFrame(size_tradeoff(rules, cfg["fitness"]["fpr_max"], SIZE_BUDGETS))
    if not tradeoff.empty:
        TAB.mkdir(parents=True, exist_ok=True)
        tradeoff.to_csv(TAB / "size_tradeoff.csv", index=False)
        print(" ->", plots.size_tradeoff(tradeoff, FIG / "06_costo_legibilidad.png",
                                         best["size_simplified"] if best else None))
    if best:
        print("\nRegla final (legible):\n ", best["sql_readable"])


if __name__ == "__main__":
    main()
