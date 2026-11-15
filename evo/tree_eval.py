"""Representación anidada de reglas, intérprete vectorizado y simplificación.

Funciona con cualquier lista prefija de nodos que tengan `name`, `arity` y
`value` (árboles de DEAP o nodos de prueba). Formato anidado:

    ("and_", a, b) | ("or_", a, b) | ("not_", a)
    ("gt", ("feat", nombre), ("q", cuantil))   umbral = cuantil de entrenamiento
    ("gt", ("feat", nombre), ("value", v))     umbral explícito (reglas manuales)
    ("lt", ...)                                 igual que gt
    ("const", True | False)
"""
from __future__ import annotations

from typing import Callable, Sequence

import numpy as np

LOGIC = {"and_", "or_", "not_"}
COMPARE = {"gt", "lt"}
ThresholdFn = Callable[[str, float], float]


def _leaf(node) -> tuple:
    value = getattr(node, "value", None)
    if isinstance(value, (bool, np.bool_)):
        return ("const", bool(value))
    if isinstance(value, (int, float, np.floating)):
        return ("q", float(value))
    return ("feat", node.name)


def to_nested(prefix: Sequence) -> tuple:
    """Convierte una lista prefija (p. ej. gp.PrimitiveTree) a tuplas anidadas."""
    pos = 0

    def build():
        nonlocal pos
        node = prefix[pos]
        pos += 1
        if node.arity == 0:
            return _leaf(node)
        children = [build() for _ in range(node.arity)]
        return (node.name, *children)

    tree = build()
    if pos != len(prefix):
        raise ValueError("Lista prefija mal formada")
    return tree


def threshold_of(cmp_node: tuple, threshold: ThresholdFn | None) -> float:
    feat, thr = cmp_node[1][1], cmp_node[2]
    if thr[0] == "value":
        return float(thr[1])
    if threshold is None:
        raise ValueError("Se necesita una tabla de cuantiles para umbrales tipo 'q'")
    return threshold(feat, thr[1])


def evaluate(tree: tuple, X: dict[str, np.ndarray], threshold: ThresholdFn | None) -> np.ndarray:
    """Máscara booleana (una posición por fila) de las filas que la regla marca."""
    n = len(next(iter(X.values())))
    op = tree[0]
    if op == "const":
        return np.full(n, tree[1], dtype=bool)
    if op == "and_":
        return evaluate(tree[1], X, threshold) & evaluate(tree[2], X, threshold)
    if op == "or_":
        return evaluate(tree[1], X, threshold) | evaluate(tree[2], X, threshold)
    if op == "not_":
        return ~evaluate(tree[1], X, threshold)
    if op in COMPARE:
        col = X[tree[1][1]]
        thr = threshold_of(tree, threshold)
        return col > thr if op == "gt" else col < thr
    raise ValueError(f"Nodo desconocido: {op}")


def simplify(tree: tuple) -> tuple:
    """Elimina constantes redundantes y dobles negaciones (equivalencia lógica)."""
    op = tree[0]
    if op in ("and_", "or_"):
        a, b = simplify(tree[1]), simplify(tree[2])
        consts = [c for c in (a, b) if c[0] == "const"]
        if op == "and_":
            if any(c[1] is False for c in consts):
                return ("const", False)
            if a == ("const", True):
                return b
            if b == ("const", True):
                return a
        else:
            if any(c[1] is True for c in consts):
                return ("const", True)
            if a == ("const", False):
                return b
            if b == ("const", False):
                return a
        if a == b:
            return a
        return (op, a, b)
    if op == "not_":
        a = simplify(tree[1])
        if a[0] == "const":
            return ("const", not a[1])
        if a[0] == "not_":
            return a[1]
        return ("not_", a)
    return tree


def size(tree: tuple) -> int:
    """Número de nodos (las comparaciones cuentan 3: operador, feature y umbral)."""
    op = tree[0]
    if op in ("const", "feat", "q", "value"):
        return 1
    return 1 + sum(size(c) for c in tree[1:])


def features_used(tree: tuple) -> set[str]:
    if tree[0] == "feat":
        return {tree[1]}
    if tree[0] in ("const", "q", "value"):
        return set()
    return set().union(*(features_used(c) for c in tree[1:]))
