"""Spec: baselines / Learning Classifier System."""
import numpy as np

from baselines import lcs
from evo.fitness import rates
from tests.helpers import synthetic_dataset

PARAMS = {"generations": 120, "pop_size": 80, "batch_size": 256}


def test_match_matrix_wildcards():
    conditions = np.array([[1, lcs.WILDCARD], [0, 0], [lcs.WILDCARD, lcs.WILDCARD]], dtype=np.int8)
    bits = np.array([[1, 0], [0, 0], [1, 1]], dtype=np.int8)
    expected = np.array([[True, False, True], [False, True, False], [True, True, True]])
    assert (lcs.match_matrix(conditions, bits) == expected).all()


def test_highest_fitness_rule_decides_and_default_is_legit():
    cuts = [("msgs_per_min", 0.5, 1.0)]
    model = lcs.LCSModel(cuts=cuts, conditions=np.array([[1], [1]], dtype=np.int8),
                         actions=np.array([0, 1], dtype=np.int8), fitness=np.array([1.0, 5.0]))
    X = {"msgs_per_min": np.array([2.0, 0.5])}
    # fila 0: casan ambas reglas y decide la de mayor aptitud (bot); fila 1: ninguna casa -> real
    assert model.predict(X).tolist() == [True, False]
    assert model.effective_rules(X) == [1] and model.size(X) == 1


def test_lcs_learns_and_is_reproducible():
    ds = synthetic_dataset(n=3000, seed=1)
    a = lcs.fit(ds, PARAMS, seed=4)
    b = lcs.fit(ds, PARAMS, seed=4)
    assert (a.predict(ds.X) == b.predict(ds.X)).all()
    assert len(a.history) == PARAMS["generations"]
    tpr, fpr = rates(a.predict(ds.X), ds.y)
    assert tpr > fpr, "debe detectar bots mejor que marcar al azar"
    assert np.mean(a.history[-20:]) > np.mean(a.history[:20])


def test_fit_predict_interface():
    ds = synthetic_dataset(n=1000, seed=2)
    mask_train, mask_test, size, model = lcs.fit_predict(ds, ds, {"seed": 3, "lcs": PARAMS})
    assert mask_train.dtype == bool and mask_train.shape == ds.y.shape == mask_test.shape
    assert size == model.size(ds.X)
