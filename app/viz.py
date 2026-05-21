"""Render simulation frames as base64 PNG. matplotlib Agg."""
from __future__ import annotations

import base64
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import simulation as sim


plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "figure.facecolor": "white",
    "axes.facecolor": "#f7f7fa",
    "axes.edgecolor": "#888",
    "axes.grid": True,
    "grid.alpha": 0.3,
})
COLOR_BASELINE = "#d4574e"
COLOR_EVOLVED = "#3d8eb9"


def _fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def _draw_field(ax, balls, title: str):
    ax.set_xlim(-2, sim.FIELD + 2)
    ax.set_ylim(-2, sim.FIELD + 2)
    ax.set_aspect("equal")
    ax.set_title(title)
    ax.add_patch(plt.Rectangle((0, 0), sim.FIELD, sim.FIELD, fill=False, edgecolor="#444", lw=2))
    ax.plot(0, 0, "ks", markersize=10)
    ax.plot(*sim.GOAL, marker="*", color="gold", markersize=18, markeredgecolor="#444")
    for i, (x, y) in enumerate(balls):
        ax.plot(x, y, "o", color="#9b59b6", markersize=12)
        ax.text(x + 0.4, y + 0.4, str(i), fontsize=8)


def trajectory_compare_png(baseline: sim.Policy, evolved: sim.Policy, sample_seed: int = 42) -> str:
    balls = sim.sample_field(sample_seed)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for ax, policy, name, color in [
        (axes[0], baseline, "Baseline (hard-coded)", COLOR_BASELINE),
        (axes[1], evolved, "AlphaGo-style Evolved", COLOR_EVOLVED),
    ]:
        _draw_field(ax, balls, name)
        path, scored, elapsed = sim.simulate(policy, balls)
        xs = [p[0] for p in path]
        ys = [p[1] for p in path]
        ax.plot(xs, ys, "-", color=color, lw=2.5, alpha=0.85)
        for i in range(len(path) - 1):
            ax.annotate(
                "",
                xy=path[i + 1],
                xytext=path[i],
                arrowprops=dict(arrowstyle="->", color=color, lw=1.3, alpha=0.7),
            )
        ax.text(
            0.02, 0.97,
            f"scored {scored}/{sim.N_BALLS}\ntime {elapsed:.1f}s",
            transform=ax.transAxes,
            fontsize=10, fontweight="bold",
            verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor=color),
        )
    fig.suptitle("Baseline vs AlphaGo-style Evolved", fontsize=13, fontweight="bold")
    fig.tight_layout()
    return _fig_to_b64(fig)


def fitness_curve_png(best_history: list[float], mean_history: list[float]) -> str:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    gens = list(range(len(best_history)))
    ax.plot(gens, best_history, "-", color=COLOR_EVOLVED, lw=2.5, label="Best")
    ax.plot(gens, mean_history, "--", color="#888", lw=1.5, label="Population mean")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Fitness")
    ax.set_title("Self-Play Evolution — Fitness Over Generations")
    ax.legend(loc="lower right")
    fig.tight_layout()
    return _fig_to_b64(fig)
