"""Specs: rule-evolution (evaluación) y sql-rule-compiler."""
import numpy as np
import pytest

from evo.data import QuantileTable
from evo.fitness import penalized_tpr, rates
from evo.to_sql import to_sql, validate_sql
from evo.tree_eval import evaluate, simplify, size, to_nested
from tests.helpers import const, feat, prim, q, synthetic_dataset


@pytest.fixture(scope="module")
def ds():
    return synthetic_dataset()


@pytest.fixture(scope="module")
def qt(ds):
    return QuantileTable(ds.X)


def test_to_nested_from_prefix():
    prefix = [prim("and_", 2), prim("gt", 2), feat("msgs_per_min"), q(0.9),
              prim("lt", 2), feat("reply_rate"), q(0.2)]
    assert to_nested(prefix) == ("and_", ("gt", ("feat", "msgs_per_min"), ("q", 0.9)),
                                 ("lt", ("feat", "reply_rate"), ("q", 0.2)))


def test_quantile_matches_numpy(ds, qt):
    for f in ("msgs_per_min", "reply_rate"):
        for qq in (0.01, 0.37, 0.9, 0.99):
            assert qt(f, qq) == pytest.approx(np.quantile(ds.X[f], qq))


def test_gt_uses_training_quantile(ds, qt):
    mask = evaluate(("gt", ("feat", "msgs_per_min"), ("q", 0.9)), ds.X, qt)
    expected = ds.X["msgs_per_min"] > np.percentile(ds.X["msgs_per_min"], 90)
    assert (mask == expected).all()


def test_true_rule_objectives(ds, qt):
    tree = to_nested([const(True)])
    tpr, fpr = rates(evaluate(tree, ds.X, qt), ds.y)
    assert (tpr, fpr, size(tree)) == (1.0, 1.0, 1)


def test_penalty_example():
    assert penalized_tpr(0.9, 0.12, 0.02, 5.0) == pytest.approx(0.4)
    assert penalized_tpr(0.9, 0.01, 0.02, 5.0) == pytest.approx(0.9)


def test_compile_simple_rule():
    tree = ("and_", ("gt", ("feat", "msgs_per_min"), ("q", 0.9)),
            ("lt", ("feat", "reply_rate"), ("q", 0.2)))
    thresholds = {("msgs_per_min", 0.9): 1.5, ("reply_rate", 0.2): 0.05}
    sql = to_sql(tree, lambda f, qq: thresholds[(f, qq)])
    assert sql == "(msgs_per_min > 1.5) AND (reply_rate < 0.05)"


def test_simplify_constants():
    tree = ("and_", ("const", True), ("gt", ("feat", "link_ratio"), ("q", 0.8)))
    sql = to_sql(tree, lambda f, qq: 0.75)
    assert "TRUE" not in sql and sql == "link_ratio > 0.75"
    assert simplify(("not_", ("not_", ("const", False)))) == ("const", False)
    assert simplify(("or_", ("const", True), ("gt", ("feat", "x"), ("q", 0.5)))) == ("const", True)


def test_simplify_preserves_semantics(ds, qt):
    import random
    from tests.helpers import random_nested
    rng = random.Random(0)
    for _ in range(200):
        t = random_nested(rng, 4)
        assert (evaluate(t, ds.X, qt) == evaluate(simplify(t), ds.X, qt)).all()


def test_sql_syntax_valid(qt):
    pytest.importorskip("sqlglot")
    import random
    from tests.helpers import random_nested
    rng = random.Random(1)
    for _ in range(50):
        assert validate_sql(to_sql(random_nested(rng, 4), qt))
