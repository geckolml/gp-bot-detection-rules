"""Learning Classifier System (modelo de Michigan simplificado) como método base.

Adaptado del cuaderno del curso "Demostración: Learning Classifier Systems"
(basado en Holland & Reitman, 1978), que resuelve la paridad de 4 bits. Se
conserva su mecánica:

- Regla = condición ternaria (0, 1, #) -> acción (0 = usuario real, 1 = bot).
- Componente de desempeño: de las reglas que casan con una entrada actúa la de
  mayor aptitud; gana `reward` si acierta y su aptitud se multiplica por
  `penalty` si falla. Una entrada sin regla que case cuenta como fallo.
- Algoritmo genético: torneo binario y mutación, sin cruce. Los hijos heredan
  la aptitud del padre y esta se acota a `fitness_cap`.

Cambios necesarios para este problema (el resto es igual al cuaderno):

1. Entradas reales -> bits. Cada feature se compara con cuantiles de
   entrenamiento (`quantile_cuts`); el bit vale 1 si la feature supera el corte.
   Son los mismos umbrales por cuantil que usan las reglas evolucionadas.
2. El entorno tiene decenas de miles de filas en lugar de 16: cada generación
   se evalúa sobre una muestra aleatoria de `batch_size` filas.
3. Con 27 bits, una condición con 1/3 de comodines (como en el cuaderno) no
   casa con casi ninguna fila. La proporción de comodines es configurable
   (`wildcard_prob`) y la mutación muestrea con esa misma proporción.
4. Para predecir, una fila sin regla que case se considera usuario real, y
   tras la última generación no se aplica el algoritmo genético (se predice
   con reglas que ya fueron evaluadas).
5. La tasa de mutación por gen baja de 0.1 a 0.03: con 27 bits, 0.1 cambia
   casi 3 genes por regla en cada generación y destruye las reglas buenas.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from evo.data import FEATURES, Dataset, QuantileTable

WILDCARD = -1

DEFAULTS = {
    "generations": 300,
    "pop_size": 200,
    "mutation_rate": 0.03,     # el cuaderno usa 0.1 con 4 bits; aquí hay 27 (ver punto 5)
    "reward": 0.1,             # igual que el cuaderno
    "penalty": 0.95,           # igual que el cuaderno
    "fitness_cap": 10.0,       # igual que el cuaderno
    "wildcard_prob": 0.85,
    "batch_size": 512,
    "quantile_cuts": [0.1, 0.5, 0.9],
}


@dataclass
class LCSModel:
    cuts: list[tuple[str, float, float]]          # (feature, cuantil, valor del corte)
    conditions: np.ndarray                        # (reglas, bits): 0, 1 o WILDCARD
    actions: np.ndarray                           # (reglas,): 0 o 1
    fitness: np.ndarray                           # (reglas,)
    history: list[float] = field(default_factory=list)  # exactitud por generación

    def predict(self, X: dict[str, np.ndarray]) -> np.ndarray:
        """Máscara de filas marcadas como bot."""
        return self._decide(X)[0] == 1

    def _decide(self, X: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
        """Acción por fila y regla que la decidió (-1 si ninguna casa)."""
        m = match_matrix(self.conditions, binarize(X, self.cuts))
        n = m.shape[1]
        action = np.zeros(n, dtype=np.int8)        # por defecto: usuario real
        decided_by = np.full(n, -1)
        pending = np.ones(n, dtype=bool)
        for r in np.argsort(-self.fitness, kind="stable"):  # mayor aptitud primero
            hit = pending & m[r]
            action[hit] = self.actions[r]
            decided_by[hit] = r
            pending &= ~hit
        return action, decided_by

    def effective_rules(self, X: dict[str, np.ndarray]) -> list[int]:
        """Reglas que deciden al menos una fila, de mayor a menor aptitud."""
        used = np.unique(self._decide(X)[1])
        used = used[used >= 0]
        return sorted(used.tolist(), key=lambda r: -self.fitness[r])

    def size(self, X: dict[str, np.ndarray]) -> int:
        """Condiciones no comodín de las reglas efectivas (comparable al número
        de comparaciones de una regla evolucionada)."""
        return sum(len(self._conditions_text(r)) for r in self.effective_rules(X))

    def _conditions_text(self, r: int) -> list[str]:
        """Condiciones de la regla r sin repetir (dos cortes de una feature
        pueden tener el mismo valor, p. ej. los cuantiles 0.1 y 0.5 iguales a 0)."""
        parts = [f"{f} {'>' if bit == 1 else '<='} {value:.4g}"
                 for (f, _, value), bit in zip(self.cuts, self.conditions[r]) if bit != WILDCARD]
        return list(dict.fromkeys(parts))

    def describe(self, X: dict[str, np.ndarray]) -> str:
        lines = []
        for r in self.effective_rules(X):
            parts = self._conditions_text(r)
            cond = " Y ".join(parts) if parts else "siempre"
            label = "bot" if self.actions[r] == 1 else "real"
            lines.append(f"SI {cond} -> {label}  (aptitud={self.fitness[r]:.2f})")
        return "\n".join(lines)


def make_cuts(X: dict[str, np.ndarray], quantiles: list[float]) -> list[tuple[str, float, float]]:
    qt = QuantileTable(X)
    return [(f, float(q), qt(f, float(q))) for f in FEATURES for q in quantiles]


def binarize(X: dict[str, np.ndarray], cuts: list[tuple[str, float, float]]) -> np.ndarray:
    return np.column_stack([X[f] > value for f, _, value in cuts]).astype(np.int8)


def match_matrix(conditions: np.ndarray, bits: np.ndarray) -> np.ndarray:
    """(reglas, filas): True si la condición casa con la fila."""
    m = np.ones((conditions.shape[0], bits.shape[0]), dtype=bool)
    for j in range(conditions.shape[1]):
        c = conditions[:, j][:, None]
        m &= (c == WILDCARD) | (c == bits[:, j][None, :])
    return m


def _random_genes(shape, wildcard_prob: float, rng: np.random.Generator) -> np.ndarray:
    genes = rng.integers(0, 2, size=shape).astype(np.int8)
    genes[rng.random(shape) < wildcard_prob] = WILDCARD
    return genes


def fit(train: Dataset, params: dict | None = None, seed: int = 1) -> LCSModel:
    p = {**DEFAULTS, **(params or {})}
    rng = np.random.default_rng(seed)
    cuts = make_cuts(train.X, p["quantile_cuts"])
    bits, y = binarize(train.X, cuts), train.y.astype(np.int8)
    n_rules, n_bits = int(p["pop_size"]), bits.shape[1]

    conditions = _random_genes((n_rules, n_bits), p["wildcard_prob"], rng)
    actions = rng.integers(0, 2, size=n_rules).astype(np.int8)
    fitness = np.ones(n_rules)
    history = []

    for gen in range(int(p["generations"])):
        # --- Componente de desempeño: actúa la regla de mayor aptitud que casa ---
        batch = rng.choice(len(y), size=min(int(p["batch_size"]), len(y)), replace=False)
        m = match_matrix(conditions, bits[batch])
        correct = 0
        for k, row in enumerate(batch):
            matching = np.flatnonzero(m[:, k])
            if matching.size == 0:
                continue
            best = matching[np.argmax(fitness[matching])]
            if actions[best] == y[row]:
                correct += 1
                fitness[best] += p["reward"]
            else:
                fitness[best] *= p["penalty"]
        history.append(correct / len(batch))
        if gen == int(p["generations"]) - 1:
            break

        # --- Algoritmo genético: torneo binario + mutación ---
        i = rng.integers(0, n_rules, size=n_rules)
        j = (i + rng.integers(1, n_rules, size=n_rules)) % n_rules   # distinto de i
        winner = np.where(fitness[i] > fitness[j], i, j)
        conditions, actions, fitness = conditions[winner], actions[winner], fitness[winner]

        mutate = rng.random(conditions.shape) < p["mutation_rate"]
        conditions = np.where(mutate, _random_genes(conditions.shape, p["wildcard_prob"], rng), conditions)
        flip = rng.random(n_rules) < p["mutation_rate"]
        actions = np.where(flip, 1 - actions, actions).astype(np.int8)
        fitness = np.minimum(fitness, p["fitness_cap"])

    return LCSModel(cuts=cuts, conditions=conditions, actions=actions, fitness=fitness, history=history)


def fit_predict(train: Dataset, test: Dataset, cfg: dict) -> tuple[np.ndarray, np.ndarray, int, LCSModel]:
    """Interfaz usada por baselines.run_baselines."""
    model = fit(train, cfg.get("lcs"), seed=int(cfg.get("seed", 1)))
    return model.predict(train.X), model.predict(test.X), model.size(train.X), model
