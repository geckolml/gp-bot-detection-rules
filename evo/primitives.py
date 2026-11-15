"""Conjunto de primitivas de Programación Genética tipada (DEAP) y generador
de árboles que respeta los tipos.

Tipos:
    bool      -> salida de la regla y de los operadores lógicos
    Feature   -> nombre de una columna de features (solo terminales)
    Quantile  -> umbral expresado como cuantil q en [0.01, 0.99] (efímero)
"""
from __future__ import annotations

import operator
import random
from inspect import isclass

from deap import gp

from evo.data import FEATURES


class Feature:
    """Marcador de tipo para terminales de feature."""


class Quantile:
    """Marcador de tipo para umbrales (cuantiles)."""


def random_quantile() -> float:
    # Función a nivel de módulo: DEAP exige la misma función para el mismo
    # nombre de efímero aunque se construya el pset varias veces.
    return round(random.uniform(0.01, 0.99), 2)


def _gt(a, b):  # las funciones no se usan para evaluar (ver tree_eval)
    return a > b


def _lt(a, b):
    return a < b


def build_pset(features: list[str] | None = None) -> gp.PrimitiveSetTyped:
    features = features or FEATURES
    pset = gp.PrimitiveSetTyped("RULE", [], bool)
    pset.addPrimitive(operator.and_, [bool, bool], bool, name="and_")
    pset.addPrimitive(operator.or_, [bool, bool], bool, name="or_")
    pset.addPrimitive(operator.not_, [bool], bool, name="not_")
    pset.addPrimitive(_gt, [Feature, Quantile], bool, name="gt")
    pset.addPrimitive(_lt, [Feature, Quantile], bool, name="lt")
    for f in features:
        pset.addTerminal(f, Feature, name=f)
    pset.addEphemeralConstant("quantile_threshold", random_quantile, Quantile)
    pset.addTerminal(True, bool)
    pset.addTerminal(False, bool)
    return pset


def generate(pset, min_: int, max_: int, condition, type_=None) -> list:
    """Versión de gp.generate que usa un terminal cuando el tipo pedido no
    tiene primitivas (Feature, Quantile). Evita el IndexError de DEAP en PG tipada.
    """
    if type_ is None:
        type_ = pset.ret
    expr = []
    height = random.randint(min_, max_)
    stack = [(0, type_)]
    while stack:
        depth, type_ = stack.pop()
        prims = pset.primitives[type_]
        if condition(height, depth) or not prims:
            terms = pset.terminals[type_]
            if not terms:
                raise IndexError(f"No hay terminales del tipo {type_}")
            term = random.choice(terms)
            if isclass(term):
                term = term()
            expr.append(term)
        else:
            prim = random.choice(prims)
            expr.append(prim)
            for arg in reversed(prim.args):
                stack.append((depth + 1, arg))
    return expr


def gen_full(pset, min_, max_, type_=None):
    return generate(pset, min_, max_, lambda h, d: d == h, type_)


def gen_grow(pset, min_, max_, type_=None):
    def condition(height, depth):
        return depth == height or (depth >= min_ and random.random() < pset.terminalRatio)
    return generate(pset, min_, max_, condition, type_)


def gen_half_and_half(pset, min_, max_, type_=None):
    method = random.choice((gen_grow, gen_full))
    return method(pset, min_, max_, type_)


def is_valid(individual) -> bool:
    """Comprueba las reglas de tipo: raíz bool y cada comparación con (Feature, Quantile)."""
    if not individual or individual[0].ret is not bool:
        return False
    for i, node in enumerate(individual):
        if node.arity:
            sl = individual.searchSubtree(i)
            child = sl.start + 1
            for arg_type in node.args:
                if individual[child].ret is not arg_type:
                    return False
                child = individual.searchSubtree(child).stop
    return True
