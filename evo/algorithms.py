"""Toolbox de DEAP y bucles evolutivos: NSGA-II (multiobjetivo) y un objetivo."""
from __future__ import annotations

import operator
import random
import time
from collections import defaultdict
from functools import partial

import numpy as np
from deap import base, creator, gp, tools

from evo import primitives
from evo.fitness import evaluate_individual

try:  # DEAP >= 1.4.2 calcula el hipervolumen con moocore
    import moocore

    def _hv_indicator(points: np.ndarray, ref: np.ndarray) -> float:
        return float(moocore.hypervolume(points, ref=ref))
except ImportError:  # pragma: no cover - DEAP <= 1.4.1 trae su propia implementación
    try:
        from deap.tools._hypervolume import hv as _hv
    except ImportError:
        from deap.tools._hypervolume import pyhv as _hv

    def _hv_indicator(points: np.ndarray, ref: np.ndarray) -> float:
        return float(_hv.hypervolume(points, ref))

# Pesos: modo multi = (TPR penalizado ↑, FPR ↓, tamaño ↓); modo single = aptitud ↑
if not hasattr(creator, "FitnessRuleMulti"):
    creator.create("FitnessRuleMulti", base.Fitness, weights=(1.0, -1.0, -1.0))
if not hasattr(creator, "FitnessRuleSingle"):
    creator.create("FitnessRuleSingle", base.Fitness, weights=(1.0,))
if not hasattr(creator, "RuleMulti"):
    creator.create("RuleMulti", gp.PrimitiveTree, fitness=creator.FitnessRuleMulti)
if not hasattr(creator, "RuleSingle"):
    creator.create("RuleSingle", gp.PrimitiveTree, fitness=creator.FitnessRuleSingle)


def max_nodes(max_height: int) -> int:
    return 2 ** (max_height + 1) - 1


# Tamaño de referencia del hipervolumen: fijo para que sea comparable entre
# corridas con distinta altura máxima (511 = árbol binario completo de altura 8).
DEFAULT_HV_REF_SIZE = max_nodes(8)


def mut_extend(individual, pset, expr):
    """Mutación de crecimiento: reemplaza un subárbol booleano x por
    and_(x, nuevo) u or_(x, nuevo), donde `nuevo` es un subárbol aleatorio.

    Es el único operador que agrega una condición sin perder la regla que ya
    funcionaba: mutUniform la reemplaza y mutInsert de DEAP completa los
    argumentos nuevos solo con las constantes True / False.
    """
    candidates = [i for i, node in enumerate(individual) if node.ret is bool]
    index = random.choice(candidates)
    slice_ = individual.searchSubtree(index)
    op = pset.mapping[random.choice(("and_", "or_"))]
    old, new = list(individual[slice_]), expr(pset=pset, type_=bool)
    individual[slice_] = [op] + (old + new if random.random() < 0.5 else new + old)
    return individual,


def cx_one_point(ind1, ind2):
    """Cruce de un punto para árboles tipados: intercambia dos subárboles del
    mismo tipo (la raíz nunca se intercambia). Es gp.cxOnePoint de DEAP con una
    diferencia: el tipo se elige de una lista ordenada por nombre.

    DEAP lo elige con random.choice(list(conjunto_de_tipos)), y el orden de un
    set de clases depende de su dirección de memoria: con la misma semilla el
    resultado cambiaba de un proceso a otro.
    """
    if len(ind1) < 2 or len(ind2) < 2:
        return ind1, ind2
    types1, types2 = defaultdict(list), defaultdict(list)
    for idx, node in enumerate(ind1[1:], 1):
        types1[node.ret].append(idx)
    for idx, node in enumerate(ind2[1:], 1):
        types2[node.ret].append(idx)
    common = sorted(set(types1) & set(types2), key=lambda t: t.__name__)
    if common:
        type_ = random.choice(common)
        slice1 = ind1.searchSubtree(random.choice(types1[type_]))
        slice2 = ind2.searchSubtree(random.choice(types2[type_]))
        ind1[slice1], ind2[slice2] = ind2[slice2], ind1[slice1]
    return ind1, ind2


def dedupe(individuals: list) -> tuple[list, list]:
    """Separa un representante por vector de objetivos del resto (clones)."""
    unique, clones, seen = [], [], set()
    for ind in individuals:
        key = ind.fitness.values
        if key in seen:
            clones.append(ind)
        else:
            seen.add(key)
            unique.append(ind)
    return unique, clones


def survivors(pool: list, mu: int, select, remove_clones: bool = True) -> list:
    """Reemplazo (μ+λ). Sin clones: la distancia de crowding no distingue
    individuos con objetivos idénticos, que quedan todos en el primer frente y
    ocupan las μ plazas. Los clones solo completan la población cuando hay
    menos de μ vectores de objetivos distintos."""
    if remove_clones:
        unique, clones = dedupe(pool)
        pool = unique + clones[:max(0, mu - len(unique))]
    return select(pool, mu)


def build_toolbox(pset, alg: dict, mode: str) -> base.Toolbox:
    tb = base.Toolbox()
    ind_cls = creator.RuleMulti if mode == "multi" else creator.RuleSingle
    tb.register("expr", primitives.gen_half_and_half, pset=pset,
                min_=alg["init_min_depth"], max_=alg["init_max_depth"])
    tb.register("individual", tools.initIterate, ind_cls, tb.expr)
    tb.register("population", tools.initRepeat, list, tb.individual)
    tb.register("evaluate", evaluate_individual)
    tb.register("mate", cx_one_point)

    # Mutación compuesta: se elige un operador al azar según sus pesos
    tb.register("expr_mut", primitives.gen_grow, min_=0, max_=2)
    ops = {
        "uniform": partial(gp.mutUniform, expr=tb.expr_mut, pset=pset),
        "node_replacement": partial(gp.mutNodeReplacement, pset=pset),
        "ephemeral": partial(gp.mutEphemeral, mode="one"),
        "extend": partial(mut_extend, pset=pset, expr=partial(primitives.gen_grow, min_=1, max_=2)),
    }
    weights = alg.get("mutation_weights",
                      {"uniform": 0.30, "node_replacement": 0.20, "ephemeral": 0.25, "extend": 0.25})
    names = list(weights)
    probs = [weights[n] for n in names]

    def mutate(ind):
        op = random.choices(names, weights=probs, k=1)[0]
        return ops[op](ind)

    tb.register("mutate", mutate)

    limit = gp.staticLimit(key=operator.attrgetter("height"), max_value=alg["max_height"])
    tb.decorate("mate", limit)
    tb.decorate("mutate", limit)

    if mode == "multi":
        tb.register("select", tools.selNSGA2)
    else:
        tb.register("select", tools.selTournament, tournsize=alg.get("tournament_size", 3))
    return tb


def _vary(offspring, tb, cxpb, mutpb):
    offspring = [tb.clone(i) for i in offspring]
    for i in range(1, len(offspring), 2):
        if random.random() < cxpb:
            offspring[i - 1], offspring[i] = tb.mate(offspring[i - 1], offspring[i])
            del offspring[i - 1].fitness.values, offspring[i].fitness.values
    for i in range(len(offspring)):
        if random.random() < mutpb:
            offspring[i], = tb.mutate(offspring[i])
            del offspring[i].fitness.values
    return offspring


def _evaluate_invalid(pop, tb, mapper) -> int:
    invalid = [ind for ind in pop if not ind.fitness.valid]
    for ind, fit in zip(invalid, mapper(tb.evaluate, invalid)):
        ind.fitness.values = fit
    return len(invalid)


def hypervolume(front, ref_size: float) -> float:
    """Hipervolumen en el espacio de minimización (1 - TPR, FPR, tamaño/ref_size)."""
    if not front:
        return 0.0
    pts = np.array([
        (1.0 - max(0.0, min(1.0, ind.fitness.values[0])), ind.fitness.values[1],
         min(1.0, ind.fitness.values[2] / ref_size))
        for ind in front
    ])
    return _hv_indicator(pts, np.array([1.0, 1.0, 1.0]))


def _stats_row(gen: int, nevals: int, pop, mode: str, elapsed: float, ref_size: float) -> dict:
    vals = np.array([ind.fitness.values for ind in pop])
    names = ["tpr_pen", "fpr", "size"] if mode == "multi" else ["fitness"]
    row = {"gen": gen, "nevals": nevals, "elapsed_s": round(elapsed, 3)}
    for j, n in enumerate(names):
        row[f"{n}_max"] = float(vals[:, j].max())
        row[f"{n}_avg"] = float(vals[:, j].mean())
        row[f"{n}_min"] = float(vals[:, j].min())
        row[f"{n}_std"] = float(vals[:, j].std())
    if mode == "multi":
        front = tools.sortNondominated(pop, len(pop), first_front_only=True)[0]
        row["front_size"] = len(front)
        row["n_unique"] = len({ind.fitness.values for ind in pop})   # diversidad
        row["hypervolume"] = hypervolume(front, ref_size)
    return row


def run_nsga2(tb, alg: dict, mapper=map, verbose: bool = True,
              hv_ref_size: float = DEFAULT_HV_REF_SIZE):
    """NSGA-II con reemplazo (μ+λ) sin clones. Devuelve (población final, frente, logbook)."""
    mu, ngen = alg["population"], alg["generations"]
    ref_size = hv_ref_size
    remove_clones = alg.get("dedupe", True)   # false solo para reproducir la ablación
    t0 = time.perf_counter()
    pop = tb.population(n=mu)
    nevals = _evaluate_invalid(pop, tb, mapper)
    pop = tb.select(pop, mu)  # asigna rango y distancia de crowding
    log = [_stats_row(0, nevals, pop, "multi", time.perf_counter() - t0, ref_size)]
    if verbose:
        print(_fmt(log[-1]))
    for gen in range(1, ngen + 1):
        if mu % 4 == 0:
            parents = tools.selTournamentDCD(pop, mu)
        else:
            parents = [random.choice(pop) for _ in range(mu)]
        offspring = _vary(parents, tb, alg["cxpb"], alg["mutpb"])
        nevals = _evaluate_invalid(offspring, tb, mapper)
        pop = survivors(pop + offspring, mu, tb.select, remove_clones)
        log.append(_stats_row(gen, nevals, pop, "multi", time.perf_counter() - t0, ref_size))
        if verbose:
            print(_fmt(log[-1]))
    front = tools.sortNondominated(pop, len(pop), first_front_only=True)[0]
    return pop, front, log


def run_single(tb, alg: dict, mapper=map, verbose: bool = True):
    """Un objetivo con torneo y elitismo. Devuelve (población, salón de la fama, logbook)."""
    mu, ngen = alg["population"], alg["generations"]
    n_elite = max(1, alg.get("elite", 1))
    t0 = time.perf_counter()
    pop = tb.population(n=mu)
    nevals = _evaluate_invalid(pop, tb, mapper)
    hof = tools.HallOfFame(max(n_elite, 10))
    hof.update(pop)
    log = [_stats_row(0, nevals, pop, "single", time.perf_counter() - t0, 1)]
    if verbose:
        print(_fmt(log[-1]))
    for gen in range(1, ngen + 1):
        elites = [tb.clone(i) for i in tools.selBest(pop, n_elite)]
        parents = tb.select(pop, mu - n_elite)
        offspring = _vary(parents, tb, alg["cxpb"], alg["mutpb"])
        nevals = _evaluate_invalid(offspring, tb, mapper)
        pop = elites + offspring
        hof.update(pop)
        log.append(_stats_row(gen, nevals, pop, "single", time.perf_counter() - t0, 1))
        if verbose:
            print(_fmt(log[-1]))
    return pop, list(hof), log


def _fmt(row: dict) -> str:
    keys = [k for k in ("gen", "nevals", "tpr_pen_max", "fpr_min", "size_avg", "hypervolume", "fitness_max", "fitness_avg") if k in row]
    return "  ".join(f"{k}={row[k]:.4g}" if isinstance(row[k], float) else f"{k}={row[k]}" for k in keys)
