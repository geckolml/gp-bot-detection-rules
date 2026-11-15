"""Utilidades de configuración YAML (sin dependencias de DEAP)."""
from __future__ import annotations

from pathlib import Path

import yaml


def load_config(path: str | Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def set_by_path(cfg: dict, dotted: str, value) -> None:
    keys = dotted.split(".")
    d = cfg
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value


def get_by_path(cfg: dict, dotted: str):
    d = cfg
    for k in dotted.split("."):
        d = d[k]
    return d
