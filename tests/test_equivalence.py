"""Spec: sql-rule-compiler / Equivalencia Python <-> SQL (requiere DuckDB)."""
import random

import numpy as np
import pandas as pd
import pytest

from evo.data import FEATURES, Dataset, QuantileTable
from evo.to_sql import to_sql
from evo.tree_eval import evaluate
from tests.helpers import random_nested, synthetic_dataset

duckdb = pytest.importorskip("duckdb")


def test_random_rules_equivalent():
    ds = synthetic_dataset(n=3000, seed=3)
    qt = QuantileTable(ds.X)
    df = ds.df.reset_index(drop=True).copy()
    df["row_id"] = np.arange(len(df))
    con = duckdb.connect()
    con.register("features_df", df)
    con.execute("create table features as select * from features_df")
    rng = random.Random(7)
    for _ in range(50):
        tree = random_nested(rng, 4)
        py = np.flatnonzero(evaluate(tree, ds.X, qt))
        sql = to_sql(tree, qt)
        got = con.execute(f"select row_id from features where {sql} order by row_id").fetchnumpy()["row_id"]
        assert np.array_equal(py, got), sql


def test_thresholds_tied_with_data_values():
    """Umbrales que coinciden con valores de la columna (features que son
    promedios o proporciones de enteros). DuckDB debe leer el literal como el
    mismo double que usa Python; si lo redondea, las filas empatadas cambian."""
    rng = np.random.default_rng(11)
    n = 4001  # q * (n - 1) es entero: el cuantil cae sobre un valor de los datos
    df = pd.DataFrame({f: rng.integers(1, 40, n) / rng.integers(1, 13, n) for f in FEATURES})
    df["is_bot"] = rng.random(n) < 0.2
    ds = Dataset.from_frame(df)
    qt = QuantileTable(ds.X)
    table = ds.df[FEATURES].copy()
    table["row_id"] = np.arange(n)
    con = duckdb.connect()
    con.register("tied_df", table)
    con.execute("create table tied as select * from tied_df")

    long_thresholds = 0
    for f in FEATURES[:4]:
        for q in np.round(np.arange(0.01, 1.0, 0.01), 2):
            thr = qt(f, float(q))
            assert (ds.X[f] == thr).any(), "el caso de prueba debe producir empates"
            long_thresholds += len(repr(thr).replace(".", "").lstrip("0")) > 15
            for op in ("gt", "lt"):
                tree = (op, ("feat", f), ("q", float(q)))
                py = np.flatnonzero(evaluate(tree, ds.X, qt))
                sql = to_sql(tree, qt)
                got = con.execute(f"select row_id from tied where {sql} order by row_id").fetchnumpy()["row_id"]
                assert np.array_equal(py, got), sql
    assert long_thresholds > 50, "el caso de prueba debe incluir umbrales de más de 15 dígitos"
