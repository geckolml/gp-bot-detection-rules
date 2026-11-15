"""Exporta reglas de una corrida a modelos dbt en dbt_project/models/moderation/.

    python -m evo.export_dbt --run results/runs/<run_id>               # regla elegida (best_rule_id)
    python -m evo.export_dbt --run results/runs/<run_id> --rules rule_00 rule_03
    python -m evo.export_dbt --run results/runs/<run_id> --all
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

MODEL_DIR = Path("dbt_project/models/moderation")

TEMPLATE = """-- Regla generada automáticamente por evo/export_dbt.py. No editar a mano.
-- corrida: {run_id} | regla: {rule_id} | nodos: {size}
-- entrenamiento: TPR={train_tpr:.4f} FPR={train_fpr:.4f}{test_line}
-- legible: {readable}
select
    scenario,
    user_id,
    window_start,
    '{model_name}' as rule_id
from {{{{ ref('fct_user_activity_hourly') }}}}
where {sql}
"""


def render_model(run_id: str, rule: dict, model_name: str) -> str:
    test_line = ""
    if "test" in rule:
        test_line = f"\n-- prueba:        TPR={rule['test']['tpr']:.4f} FPR={rule['test']['fpr']:.4f}"
    return TEMPLATE.format(
        run_id=run_id, rule_id=rule["rule_id"], size=rule["size_simplified"],
        train_tpr=rule["train"]["tpr"], train_fpr=rule["train"]["fpr"], test_line=test_line,
        readable=rule["sql_readable"], model_name=model_name, sql=rule["sql"],
    )


def export(run_dir: Path, rule_ids: list[str] | None = None, all_rules: bool = False,
           model_dir: Path = MODEL_DIR) -> list[Path]:
    rules = json.loads((run_dir / "pareto.json").read_text())
    summary = json.loads((run_dir / "summary.json").read_text())
    if all_rules:
        chosen = rules
    else:
        ids = rule_ids or [summary["best_rule_id"]]
        if ids == [None]:
            raise SystemExit("La corrida no tiene una regla factible; usa --rules o --all")
        chosen = [r for r in rules if r["rule_id"] in ids]
    model_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for r in chosen:
        name = f"flag_bots_{r['rule_id']}"
        path = model_dir / f"{name}.sql"
        path.write_text(render_model(summary["run_id"], r, name))
        written.append(path)
        print(f"-> {path}")
    return written


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--rules", nargs="*")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    export(args.run, args.rules, args.all)


if __name__ == "__main__":
    main()
