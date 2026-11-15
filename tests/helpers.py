"""Utilidades de test que no dependen de DEAP ni de DuckDB."""
from __future__ import annotations

import random
from dataclasses import dataclass

import numpy as np
import pandas as pd

from evo.data import FEATURES, Dataset


@dataclass
class Node:
    """Nodo mínimo compatible con la interfaz de DEAP (name, arity, value)."""
    name: str
    arity: int = 0
    value: object = None


def prim(name: str, arity: int) -> Node:
    return Node(name, arity)


def feat(name: str) -> Node:
    return Node(name, 0, name)


def q(v: float) -> Node:
    return Node(str(v), 0, v)


def const(v: bool) -> Node:
    return Node(str(v), 0, v)


def random_nested(rng: random.Random, depth: int = 3) -> tuple:
    """Regla aleatoria en formato anidado (para pruebas de equivalencia)."""
    if depth == 0 or rng.random() < 0.3:
        if rng.random() < 0.1:
            return ("const", rng.random() < 0.5)
        op = rng.choice(["gt", "lt"])
        return (op, ("feat", rng.choice(FEATURES)), ("q", round(rng.uniform(0.01, 0.99), 2)))
    op = rng.choice(["and_", "or_", "not_"])
    if op == "not_":
        return (op, random_nested(rng, depth - 1))
    return (op, random_nested(rng, depth - 1), random_nested(rng, depth - 1))


def synthetic_dataset(n: int = 2000, seed: int = 0, bot_frac: float = 0.2) -> Dataset:
    rng = np.random.default_rng(seed)
    y = rng.random(n) < bot_frac
    df = pd.DataFrame({f: rng.gamma(2.0, 1.0, n) for f in FEATURES})
    df["msgs_per_min"] += y * rng.gamma(3.0, 1.0, n)        # señal
    df["reply_rate"] = np.clip(rng.beta(5, 2, n) - y * 0.5, 0, 1)
    df["is_bot"] = y
    df["agent_type"] = np.where(y, "naive_bot", "legit")
    return Dataset.from_frame(df)
