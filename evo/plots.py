"""Figuras para el informe (matplotlib, PNG)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

# Paleta categórica en orden fijo (nunca reciclada) y tinta de texto neutra.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
INK, INK_2, GRID = "#1f1f1e", "#5f5e5a", "#e4e3df"

plt.rcParams.update({
    "figure.dpi": 130, "savefig.bbox": "tight", "font.size": 10,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "axes.titlecolor": INK,
    "axes.titleweight": "bold", "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "xtick.color": INK_2, "ytick.color": INK_2, "legend.frameon": False,
    "lines.linewidth": 2.0,
})


def _save(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


def _band(ax, logs: list[pd.DataFrame], col: str, color: str, label: str, style: str = "-"):
    g = logs[0]["gen"].to_numpy()
    m = np.vstack([lg[col].to_numpy() for lg in logs])
    mean, std = m.mean(0), m.std(0)
    ax.plot(g, mean, style, color=color, label=label)
    if len(logs) > 1:
        ax.fill_between(g, mean - std, mean + std, color=color, alpha=0.15, linewidth=0)


def convergence(logs: list[pd.DataFrame], out: Path, title: str = "") -> Path:
    """Mejor y promedio de cada objetivo por generación (media ± 1 desv. entre semillas)."""
    multi = "tpr_pen_max" in logs[0]
    if multi:
        fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
        specs = [("tpr_pen", "TPR penalizado (↑)", "max"), ("fpr", "FPR (↓)", "min"), ("size", "Tamaño en nodos (↓)", "min")]
        for ax, (k, lab, best) in zip(axes, specs):
            _band(ax, logs, f"{k}_{best}", SERIES[0], "mejor")
            _band(ax, logs, f"{k}_avg", SERIES[1], "promedio", "--")
            ax.set_title(lab)
            ax.set_xlabel("generación")
        axes[0].legend(loc="lower right")
    else:
        fig, ax = plt.subplots(figsize=(6, 3.6))
        _band(ax, logs, "fitness_max", SERIES[0], "mejor")
        _band(ax, logs, "fitness_avg", SERIES[1], "promedio", "--")
        ax.set_title("Aptitud (↑)")
        ax.set_xlabel("generación")
        ax.legend(loc="lower right")
    if title:
        fig.suptitle(title, color=INK)
    return _save(fig, out)


def hypervolume(logs: list[pd.DataFrame], out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6, 3.6))
    _band(ax, logs, "hypervolume", SERIES[0], "hipervolumen")
    ax.set_title("Hipervolumen del frente no dominado")
    ax.set_xlabel("generación")
    return _save(fig, out)


def pareto(rules: list[dict], baselines: pd.DataFrame | None, out: Path, split: str = "test",
           fpr_max: float | None = None) -> Path:
    """TPR vs FPR de las reglas del frente; métodos base como marcadores con etiqueta."""
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    fpr = [r[split]["fpr"] for r in rules]
    tpr = [r[split]["tpr"] for r in rules]
    sz = [r["size_simplified"] for r in rules]
    sc = ax.scatter(fpr, tpr, c=sz, cmap="Blues", vmin=0, s=42, edgecolors="white", linewidths=1.5,
                    label="PG + NSGA-II (color = nodos)")
    fig.colorbar(sc, ax=ax, label="nodos de la regla")
    if baselines is not None:
        b = baselines[baselines.scenario == split]
        markers = ["s", "^", "D", "v", "P"]
        for i, (_, row) in enumerate(b.iterrows()):
            ax.scatter(row.fpr, row.tpr, marker=markers[i % len(markers)], s=64,
                       color=SERIES[(i + 1) % len(SERIES)], edgecolors="white", linewidths=1.5, label=row.method)
    if fpr_max is not None:
        ax.axvline(fpr_max, color=INK_2, linestyle=":", linewidth=1.2)
        ax.text(fpr_max, 0.02, f"FPR = {fpr_max:g} ", color=INK_2, fontsize=8, ha="right")
    ax.set_xlabel("FPR (usuarios reales marcados)")
    ax.set_ylabel("TPR (bots detectados)")
    ax.set_ylim(0, 1.02)
    ax.set_title(f"Frente de Pareto vs métodos base ({split})")
    ax.legend(loc="lower right", fontsize=8)
    return _save(fig, out)


def sensitivity(table: pd.DataFrame, out: Path, metric: str = "hv", ylabel: str = "hipervolumen final") -> Path:
    params = [c for c in table.columns if c.startswith("algorithm.")]
    fig, axes = plt.subplots(1, len(params), figsize=(3.4 * len(params), 3.4), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, p in zip(axes, params):
        others = [q for q in params if q != p]
        # en diseño uno a la vez: filas donde los demás parámetros están en su valor modal (base)
        base_vals = {q: table[q].mode().iloc[0] for q in others}
        sub = table
        for q, v in base_vals.items():
            sub = sub[sub[q] == v]
        sub = sub.sort_values(p)
        ax.errorbar(sub[p].astype(str), sub[f"{metric}_mean"], yerr=sub[f"{metric}_std"],
                    color=SERIES[0], marker="o", markersize=7, capsize=4)
        ax.set_title(p.split(".")[-1])
    axes[0].set_ylabel(ylabel)
    return _save(fig, out)


def train_vs_test(rows: pd.DataFrame, out: Path) -> Path:
    """TPR en entrenamiento vs prueba por método (barras agrupadas)."""
    methods = list(dict.fromkeys(rows.method))
    x = np.arange(len(methods))
    w = 0.38
    fig, ax = plt.subplots(figsize=(1.4 * len(methods) + 2, 3.8))
    for j, split in enumerate(("train", "test")):
        vals = [rows[(rows.method == m) & (rows.scenario == split)].tpr.mean() for m in methods]
        ax.bar(x + (j - 0.5) * w, vals, width=w - 0.02, color=SERIES[j], label=split)
    ax.set_xticks(x, methods, rotation=20, ha="right")
    ax.set_ylabel("TPR")
    ax.set_ylim(0, 1.18)   # espacio para la leyenda sobre las barras
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.set_title("Generalización: entrenamiento vs prueba (bot no visto)")
    ax.legend(loc="upper right", ncol=2)
    return _save(fig, out)


def size_tradeoff(table: pd.DataFrame, out: Path, chosen_size: int | None = None) -> Path:
    """Costo de la legibilidad: TPR de la mejor regla factible según su número de nodos."""
    t = table.drop_duplicates("rule_id").sort_values("size")
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    series = [("train_tpr", "entrenamiento", "-"), ("test_tpr", "prueba", "-"),
              ("test_tpr_stealth_bot", "prueba: solo bot sigiloso", "--")]
    for (col, label, style), color in zip(series, SERIES):
        if col not in t:
            continue
        ax.plot(t["size"], t[col], style, color=color, marker="o", markersize=6, label=label)
        # etiqueta directa del último valor, en tinta neutra (la identidad la da la línea)
        ax.annotate(f"{t[col].iloc[-1]:.2f}", (t["size"].iloc[-1], t[col].iloc[-1]),
                    xytext=(6, 0), textcoords="offset points", va="center", color=INK_2, fontsize=8)
    if chosen_size is not None:
        ax.axvline(chosen_size, color=INK_2, linestyle=":", linewidth=1.2)
        ax.text(chosen_size, 0.03, " regla final", color=INK_2, fontsize=8)
    ax.set_xlabel("nodos de la regla")
    ax.set_ylabel("TPR (bots detectados)")
    ax.set_ylim(0, 1.02)
    ax.set_xlim(0, t["size"].max() * 1.1)
    ax.set_title("Costo de la legibilidad: detección según el tamaño de la regla")
    ax.legend(loc="center right", bbox_to_anchor=(1.0, 0.62))
    return _save(fig, out)
