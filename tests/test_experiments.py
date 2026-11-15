"""Specs: experiment-analysis (sensibilidad) y baselines (umbral restringido)."""
import numpy as np
import pytest

from evo.sensitivity import expand_design


def test_one_at_a_time_design():
    base = {"algorithm": {"population": 200, "mutpb": 0.2}}
    params = {"algorithm.population": [100, 200, 400], "algorithm.mutpb": [0.1, 0.2, 0.4]}
    combos = expand_design(base, params, "one_at_a_time")
    assert len(combos) == 5            # (3 + 3 - 1)
    assert len(combos) * 5 == 25       # con 5 semillas
    assert combos[0] == {"algorithm.population": 200, "algorithm.mutpb": 0.2}


def test_full_design():
    base = {"algorithm": {"population": 200, "mutpb": 0.2}}
    params = {"algorithm.population": [100, 200], "algorithm.mutpb": [0.1, 0.2, 0.4]}
    assert len(expand_design(base, params, "full")) == 6


def test_base_value_must_be_listed():
    with pytest.raises(ValueError):
        expand_design({"algorithm": {"population": 300}}, {"algorithm.population": [100, 200]})


def test_logistic_threshold_respects_fpr():
    pytest.importorskip("sklearn")
    from baselines.run_baselines import threshold_at_fpr
    rng = np.random.default_rng(0)
    neg = rng.normal(size=5000)
    for eps in (0.0, 0.01, 0.02, 0.1):
        t = threshold_at_fpr(neg, eps)
        assert (neg > t).mean() <= eps
