"""CLI del simulador.

    python -m simulator.simulate --scenario all
    python -m simulator.simulate --scenario train --config simulator/config.yaml
"""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from simulator.agents import Scenario, simulate


def load_config(path: str | Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def get_scenario(config: dict, name: str) -> Scenario:
    s = config["scenarios"][name]
    return Scenario(name=name, seed=int(s["seed"]), counts=dict(s["counts"]))


def write_scenario(tables: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_parquet(out_dir / f"{name}.parquet", index=False)


def main() -> None:
    ap = argparse.ArgumentParser(description="Simulador de actividad (usuarios reales y bots)")
    ap.add_argument("--config", default="simulator/config.yaml")
    ap.add_argument("--scenario", default="all", help="train, test o all")
    args = ap.parse_args()

    config = load_config(args.config)
    names = list(config["scenarios"]) if args.scenario == "all" else [args.scenario]
    for name in names:
        tables = simulate(get_scenario(config, name), config)
        out = Path(config["output_dir"]) / name
        write_scenario(tables, out)
        u, m = tables["users"], tables["messages"]
        print(f"[{name}] usuarios={len(u)} (bots={int(u.is_bot.sum())}) "
              f"mensajes={len(m)} ubicaciones={len(tables['locations'])} -> {out}")


if __name__ == "__main__":
    main()
