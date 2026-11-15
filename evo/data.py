"""Carga de features desde DuckDB y tabla de cuantiles de entrenamiento."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# Variables de decisión disponibles para las reglas (columnas de
# fct_user_activity_hourly). No incluir is_bot ni agent_type.
FEATURES: list[str] = [
    "msgs_count",
    "msgs_per_min",
    "unique_recipients",
    "link_ratio",
    "dup_template_ratio",
    "avg_msg_len",
    "reply_rate",
    "account_age_hours",
    "max_geo_speed_kmh",
]


@dataclass
class Dataset:
    """Features como columnas numpy + etiqueta + tipo de agente (solo análisis)."""
    X: dict[str, np.ndarray]
    y: np.ndarray
    agent_type: np.ndarray
    df: pd.DataFrame = field(repr=False)

    @property
    def n(self) -> int:
        return len(self.y)

    @classmethod
    def from_frame(cls, df: pd.DataFrame) -> "Dataset":
        df = df.reset_index(drop=True)
        X = {f: df[f].to_numpy(dtype=np.float64) for f in FEATURES}
        y = df["is_bot"].to_numpy(dtype=bool)
        agent = df["agent_type"].to_numpy() if "agent_type" in df else np.array(["?"] * len(df))
        return cls(X=X, y=y, agent_type=agent, df=df)

    def subsample(self, max_rows: int | None, seed: int) -> "Dataset":
        """Submuestreo estratificado por etiqueta (conserva la proporción de bots)."""
        if not max_rows or self.n <= max_rows:
            return self
        rng = np.random.default_rng(seed)
        frac = max_rows / self.n
        idx = np.concatenate([
            rng.choice(np.flatnonzero(self.y == v), size=max(1, int(round(frac * (self.y == v).sum()))), replace=False)
            for v in (True, False)
        ])
        return Dataset.from_frame(self.df.iloc[np.sort(idx)])


def load_features(warehouse: str, scenario: str, table: str = "fct_user_activity_hourly") -> Dataset:
    import duckdb

    con = duckdb.connect(warehouse, read_only=True)
    try:
        cols = ", ".join(["scenario", "user_id", "window_start", *FEATURES, "is_bot", "agent_type"])
        df = con.execute(
            f"select {cols} from {table} where scenario = ? order by user_id, window_start", [scenario]
        ).df()
    finally:
        con.close()
    if df.empty:
        raise ValueError(f"No hay filas para el escenario '{scenario}' en {warehouse}:{table}. ¿Corriste make data y make features?")
    return Dataset.from_frame(df)


class QuantileTable:
    """Cuantiles de cada feature en entrenamiento.

    `value(f, q)` replica np.quantile(..., method='linear') sobre la columna
    ordenada, con caché, porque los umbrales efímeros se redondean a 2
    decimales y se repiten mucho.
    """

    def __init__(self, X: dict[str, np.ndarray]):
        self._sorted = {f: np.sort(v) for f, v in X.items()}
        self._cache: dict[tuple[str, float], float] = {}

    def value(self, feature: str, q: float) -> float:
        key = (feature, float(q))
        if key not in self._cache:
            s = self._sorted[feature]
            pos = float(q) * (len(s) - 1)
            lo = int(np.floor(pos))
            hi = min(lo + 1, len(s) - 1)
            frac = pos - lo
            self._cache[key] = float(s[lo] + (s[hi] - s[lo]) * frac)
        return self._cache[key]

    __call__ = value

    def grid(self, step: float = 0.01) -> dict[str, list[float]]:
        qs = np.round(np.arange(0, 1 + 1e-9, step), 4)
        return {f: [self.value(f, q) for q in qs] for f in self._sorted}
