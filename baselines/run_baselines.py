"""Métodos de referencia evaluados con las mismas métricas que las reglas evolucionadas.

    python -m baselines.run_baselines --config experiments/base.yaml
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from baselines import lcs
from evo.data import FEATURES, Dataset, load_features
from evo.fitness import metrics_by_type
from evo.config import load_config
from evo.to_sql import to_sql
from evo.tree_eval import evaluate, size

OUT = Path("results/tables")

# Regla escrita "a mano", como la escribiría un analista sin optimización.
MANUAL_RULE = (
    "or_",
    ("gt", ("feat", "msgs_per_min"), ("value", 0.5)),
    ("or_",
     ("and_",
      ("gt", ("feat", "link_ratio"), ("value", 0.5)),
      ("lt", ("feat", "account_age_hours"), ("value", 48.0))),
     ("gt", ("feat", "max_geo_speed_kmh"), ("value", 900.0))),
)


def matrix(ds: Dataset) -> np.ndarray:
    return np.column_stack([ds.X[f] for f in FEATURES])


def threshold_at_fpr(neg_scores: np.ndarray, fpr_max: float) -> float:
    """Umbral t tal que la proporción de negativos con score > t es <= fpr_max."""
    s = np.sort(neg_scores)[::-1]
    k = int(np.floor(fpr_max * len(s)))
    if k >= len(s):
        return -np.inf
    return float(s[k])


def tree_to_sql(clf: DecisionTreeClassifier, feature_names: list[str]) -> str:
    """Disyunción de las ramas del árbol cuyas hojas predicen bot."""
    t = clf.tree_
    paths = []

    def walk(node: int, conds: list[str]):
        if t.children_left[node] == -1:
            if np.argmax(t.value[node][0]) == 1:
                paths.append(" AND ".join(conds) if conds else "TRUE")
            return
        f, thr = feature_names[t.feature[node]], t.threshold[node]
        walk(t.children_left[node], conds + [f"{f} <= {thr:.6g}"])
        walk(t.children_right[node], conds + [f"{f} > {thr:.6g}"])

    walk(0, [])
    return " OR\n".join(f"({p})" for p in paths) if paths else "FALSE"


def run(cfg: dict, train: Dataset, test: Dataset) -> pd.DataFrame:
    fpr_max = cfg["fitness"]["fpr_max"]
    rows = []

    def record(method: str, size_: int, mask_train: np.ndarray, mask_test: np.ndarray):
        for split, ds, m in (("train", train, mask_train), ("test", test, mask_test)):
            rows.append({"method": method, "scenario": split, "size": size_,
                         **metrics_by_type(m, ds.y, ds.agent_type)})

    # 1. Regla manual
    record("manual_rule", size(MANUAL_RULE),
           evaluate(MANUAL_RULE, train.X, None), evaluate(MANUAL_RULE, test.X, None))
    (OUT / "baseline_manual_rule.sql").write_text(to_sql(MANUAL_RULE) + "\n")

    Xtr, Xte = matrix(train), matrix(test)

    # 2. Árboles de decisión
    for depth in (3, 5):
        clf = DecisionTreeClassifier(max_depth=depth, class_weight="balanced", random_state=0)
        clf.fit(Xtr, train.y)
        record(f"decision_tree_d{depth}", int(clf.tree_.node_count),
               clf.predict(Xtr).astype(bool), clf.predict(Xte).astype(bool))
        (OUT / f"baseline_tree_depth{depth}.sql").write_text(tree_to_sql(clf, FEATURES) + "\n")

    # 3. Regresión logística con umbral restringido a FPR <= fpr_max en entrenamiento
    lr = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000))
    lr.fit(Xtr, train.y)
    s_tr, s_te = lr.decision_function(Xtr), lr.decision_function(Xte)
    thr = threshold_at_fpr(s_tr[~train.y], fpr_max)
    record("logistic_regression", len(FEATURES) + 1, s_tr > thr, s_te > thr)

    # 4. Learning Classifier System adaptado del cuaderno del curso
    mask_train, mask_test, lcs_size, model = lcs.fit_predict(train, test, cfg)
    record("lcs", lcs_size, mask_train, mask_test)
    (OUT / "baseline_lcs_rules.txt").write_text(model.describe(train.X) + "\n")

    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="experiments/base.yaml")
    args = ap.parse_args()
    cfg = load_config(args.config)
    d = cfg["data"]
    train = load_features(d["warehouse"], d["train_scenario"], d["table"]).subsample(d.get("max_train_rows"), cfg["seed"])
    test = load_features(d["warehouse"], d["test_scenario"], d["table"])
    OUT.mkdir(parents=True, exist_ok=True)
    df = run(cfg, train, test)
    df.to_csv(OUT / "baselines.csv", index=False)
    print(df.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
