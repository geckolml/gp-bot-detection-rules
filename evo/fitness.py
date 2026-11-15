"""Objetivos de aptitud: TPR (recall de bots), FPR y tamaño de la regla."""
from __future__ import annotations

import numpy as np

from evo.data import Dataset, QuantileTable
from evo.tree_eval import evaluate, to_nested


def rates(mask: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    pos, neg = y, ~y
    tpr = float(mask[pos].mean()) if pos.any() else 0.0
    fpr = float(mask[neg].mean()) if neg.any() else 0.0
    return tpr, fpr


def penalized_tpr(tpr: float, fpr: float, fpr_max: float, lam: float) -> float:
    """Penalización por violar FPR <= fpr_max (tratamiento de restricciones)."""
    return tpr - lam * max(0.0, fpr - fpr_max)


def single_objective(tpr: float, fpr: float, size: int, fpr_weight: float, parsimony: float) -> float:
    return tpr - fpr_weight * fpr - parsimony * size


def metrics_by_type(mask: np.ndarray, y: np.ndarray, agent_type: np.ndarray) -> dict[str, float]:
    """TPR por tipo de bot y FPR global (análisis de generalización)."""
    tpr, fpr = rates(mask, y)
    out = {"tpr": tpr, "fpr": fpr}
    for t in sorted(set(agent_type[y])):
        sel = agent_type == t
        out[f"tpr_{t}"] = float(mask[sel].mean())
    return out


# --- Estado global para evaluación en paralelo (multiprocessing con fork) ---
_STATE: dict = {}


def init_state(train: Dataset, qtable: QuantileTable, cfg_fitness: dict, mode: str) -> None:
    _STATE.update(train=train, qtable=qtable, cfg=cfg_fitness, mode=mode)


def evaluate_individual(individual) -> tuple:
    """Función de aptitud registrada en el toolbox de DEAP."""
    train: Dataset = _STATE["train"]
    cfg = _STATE["cfg"]
    tree = to_nested(individual)
    mask = evaluate(tree, train.X, _STATE["qtable"])
    tpr, fpr = rates(mask, train.y)
    n = len(individual)
    if _STATE["mode"] == "multi":
        return (penalized_tpr(tpr, fpr, cfg["fpr_max"], cfg["penalty_lambda"]), fpr, float(n))
    return (single_objective(tpr, fpr, n, cfg["single_fpr_weight"], cfg["parsimony"]),)
