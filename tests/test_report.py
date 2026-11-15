"""Spec: experiment-analysis / Corrida principal del reporte."""
import os

import pytest

pytest.importorskip("matplotlib")

from evo.report import pick_main_run  # noqa: E402


def make_run(path, mtime):
    path.mkdir(parents=True)
    summary = path / "summary.json"
    summary.write_text("{}")
    os.utime(summary, (mtime, mtime))
    return path


def test_main_run_ignores_later_sensitivity_runs(tmp_path):
    make_run(tmp_path / "base_antigua", 1000)
    base = make_run(tmp_path / "base_reciente", 2000)
    make_run(tmp_path / "sensitivity" / "population400_s5", 3000)   # posterior a la corrida base
    assert pick_main_run(tmp_path) == base


def test_main_run_falls_back_to_subfolders(tmp_path):
    make_run(tmp_path / "sensitivity" / "a", 1000)
    last = make_run(tmp_path / "sensitivity" / "b", 2000)
    assert pick_main_run(tmp_path) == last
    assert pick_main_run(tmp_path / "vacia") is None
