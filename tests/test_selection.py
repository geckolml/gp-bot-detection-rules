"""Specs: rule-evolution / Selección de la regla final y experiment-analysis / sensibilidad."""
import json

import pytest

from evo.run import best_on_test, select_final_rule, size_tradeoff
from evo.sensitivity import aggregate


def rule(rule_id, size, train, test):
    return {"rule_id": rule_id, "size_simplified": size, "sql_readable": rule_id,
            "train": {"tpr": train[0], "fpr": train[1]}, "test": {"tpr": test[0], "fpr": test[1]}}


def test_test_metrics_do_not_intervene():
    rules = [rule("mejor_en_train", 7, (0.90, 0.010), (0.50, 0.03)),
             rule("mejor_en_test", 7, (0.80, 0.010), (0.95, 0.00))]
    assert select_final_rule(rules, 0.02)["rule_id"] == "mejor_en_train"
    assert best_on_test(rules, 0.02)["rule_id"] == "mejor_en_test"   # la cota superior sí mira la prueba


def test_constraint_is_checked_on_train():
    rules = [rule("viola_en_train", 3, (0.99, 0.05), (0.99, 0.00)),
             rule("cumple", 3, (0.70, 0.02), (0.60, 0.04))]
    assert select_final_rule(rules, 0.02)["rule_id"] == "cumple"


def test_size_budget():
    rules = [rule("grande", 40, (0.99, 0.01), (0.9, 0.01)),
             rule("mediana", 15, (0.97, 0.01), (0.8, 0.01)),
             rule("chica", 7, (0.95, 0.01), (0.8, 0.01))]
    assert select_final_rule(rules, 0.02, max_size=15)["rule_id"] == "mediana"
    assert select_final_rule(rules, 0.02, max_size=None)["rule_id"] == "grande"
    assert [r["rule_id"] for r in size_tradeoff(rules, 0.02, [3, 7, 15, None])] == ["chica", "mediana", "grande"]


def test_tie_prefers_smaller_rule():
    rules = [rule("larga", 11, (0.9, 0.01), (0.9, 0.01)), rule("corta", 7, (0.9, 0.01), (0.1, 0.01))]
    assert select_final_rule(rules, 0.02)["rule_id"] == "corta"


def test_no_feasible_rule():
    rules = [rule("a", 7, (0.9, 0.10), (0.9, 0.0)), rule("b", 31, (0.9, 0.01), (0.9, 0.0))]
    assert select_final_rule(rules, 0.02, max_size=15) is None


def test_sensitivity_table_has_final_rule_columns(tmp_path):
    dirs = []
    for seed, tpr_test in ((1, 0.80), (2, 0.90)):
        d = tmp_path / f"population200_s{seed}"
        d.mkdir()
        rules = [rule("final", 7, (0.9, 0.01), (tpr_test, 0.01)), rule("grande", 40, (0.99, 0.01), (0.99, 0.01))]
        (d / "pareto.json").write_text(json.dumps(rules))
        (d / "combo.json").write_text(json.dumps({"algorithm.population": 200}))
        (d / "summary.json").write_text(json.dumps(
            {"seed": seed, "hypervolume_final": 0.9, "best_test_tpr_feasible": 0.99, "runtime_s": 1.0}))
        dirs.append(d)
    table = aggregate(dirs, fpr_max=0.02, max_size=15)
    assert len(table) == 1
    assert table.tpr_final_test_mean.iloc[0] == pytest.approx(0.85)   # usa la regla de 7 nodos, no la de 40
    assert {"tpr_final_test_std", "hv_mean", "hv_std", "runtime_mean"} <= set(table.columns)
