"""Matplotlib plots: tactical map, dispersion, information map, benchmark charts."""

from __future__ import annotations

import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Circle
from matplotlib.patches import Rectangle

from .config import AMBER, CYAN, GREEN, MAP_BG, ORANGE, RED, SENSOR_NAMES, SENSOR_XY, SITE_SIZE
from .inference import InferenceResult
from .physics import gaussian_plume


# ------------------------------- Plot helpers --------------------------------
def make_glow(scale: float) -> LinearSegmentedColormap:
    stops = [
        (0.00, (0.99, 0.45, 0.09, 0.00)),
        (0.20, (0.80, 0.30, 0.05, 0.25 * scale)),
        (0.50, (0.98, 0.45, 0.09, 0.60 * scale)),
        (0.80, (1.00, 0.68, 0.25, 0.88 * scale)),
        (1.00, (1.00, 0.96, 0.75, min(1.0, 1.0 * scale))),
    ]
    return LinearSegmentedColormap.from_list("glow", stops)


GLOW = make_glow(1.0)
GLOW_HALO = make_glow(0.45)
PLUME_CMAP = LinearSegmentedColormap.from_list(
    "plume", [MAP_BG, "#3b0f70", "#8c2981", "#de4968", "#fe9f6d", "#fcfdbf"]
)
INFO_CMAP = LinearSegmentedColormap.from_list(
    "info", ["#0e1726", "#1d4ed8", "#22d3ee", "#fbbf24", "#fff7d6"]
)


def smooth2d(a: np.ndarray, sigma: float) -> np.ndarray:
    if sigma <= 0:
        return a
    r = int(3 * sigma) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    a = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 0, a)
    a = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 1, a)
    return a


def posterior_density(result: InferenceResult, bins: int = 60):
    hist, xe, ye = np.histogram2d(
        result.particles[:, 0], result.particles[:, 1], bins=bins,
        range=[[0, SITE_SIZE], [0, SITE_SIZE]], weights=result.weights
    )
    xc, yc = (xe[:-1] + xe[1:]) / 2, (ye[:-1] + ye[1:]) / 2
    return xc, yc, hist.T


def style_map_axes(fig, ax, labels: bool = True) -> None:
    fig.patch.set_facecolor(MAP_BG)
    ax.set_facecolor(MAP_BG)
    for spine in ax.spines.values():
        spine.set_color("#2a3b57")
        spine.set_linewidth(1.2)
    ax.tick_params(colors="#64748b", labelsize=8)
    ax.set_xlim(0, SITE_SIZE)
    ax.set_ylim(0, SITE_SIZE)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks(np.arange(0, 101, 20))
    ax.set_yticks(np.arange(0, 101, 20))
    ax.set_xticks(np.arange(0, 101, 10), minor=True)
    ax.set_yticks(np.arange(0, 101, 10), minor=True)
    ax.grid(which="major", color="#1f2d46", linewidth=0.8)
    ax.grid(which="minor", color="#15223a", linewidth=0.5)
    ax.tick_params(which="minor", length=0)
    ax.set_axisbelow(True)
    if labels:
        ax.set_xlabel("X / East (m)", color="#94a3b8", fontsize=9)
        ax.set_ylabel("Y / North (m)", color="#94a3b8", fontsize=9)


def style_generic_axes(fig, ax) -> None:
    fig.patch.set_facecolor(MAP_BG)
    ax.set_facecolor(MAP_BG)
    for side, spine in ax.spines.items():
        spine.set_color("#2a3b57")
        if side in ("top", "right"):
            spine.set_visible(False)
    ax.tick_params(colors="#94a3b8", labelsize=8)
    ax.grid(color="#1f2d46", linewidth=0.7, alpha=0.8)
    ax.set_axisbelow(True)
    ax.xaxis.label.set_color("#94a3b8")
    ax.yaxis.label.set_color("#94a3b8")
    ax.title.set_color("#e2e8f0")


def draw_tactical_map(result: InferenceResult, readings, k: int, layers: set, threshold: float,
                      truth=None, active_point=None, baseline_xy=None, figsize=(12.0, 7.4), mobile=None):
    """mobile = {"start": (x, y), "trail": [(x, y, reading), ...], "route_to": (x, y) | None}"""
    fig, ax = plt.subplots(figsize=figsize)
    style_map_axes(fig, ax)
    ex, ey, eq, eu, etheta = result.mean
    extra_handles = []

    if "posterior" in layers:
        xc, yc, dens = posterior_density(result)
        X, Y = np.meshgrid(xc, yc)
        diffuse = result.ess > 0.5 * len(result.weights)
        s_halo, s_core = (6.0, 3.2) if diffuse else (3.2, 1.4)
        for sigma, cmap in ((s_halo, GLOW_HALO), (s_core, GLOW)):
            d = smooth2d(dens, sigma)
            if d.max() > 0:
                ax.contourf(X, Y, d / d.max(), levels=np.linspace(0.05, 1.001, 15), cmap=cmap, zorder=2)
        d = smooth2d(dens, s_core)
        if d.max() > 0:
            ax.contour(X, Y, d / d.max(), levels=[0.3, 0.6, 0.85],
                       colors=["#ffb347", "#ffd08a", "#fff1c9"], linewidths=[0.7, 1.0, 1.3],
                       alpha=0.9, zorder=3)
        extra_handles.append(Line2D([0], [0], color=ORANGE, lw=7, alpha=0.75, label="Posterior probability"))

    if "wind" in layers:
        qx = np.linspace(8, 92, 8)
        QX, QY = np.meshgrid(qx, qx)
        bearing = math.radians((etheta + 180.0) % 360.0)
        length = 4.6
        ax.quiver(QX, QY, np.full_like(QX, math.sin(bearing) * length), np.full_like(QY, math.cos(bearing) * length),
                  angles="xy", scale_units="xy", scale=1, color=CYAN, alpha=0.25, width=0.0024,
                  headwidth=4.2, headlength=5, zorder=1)
        extra_handles.append(Line2D([0], [0], color=CYAN, lw=2, alpha=0.6, label="Estimated wind flow"))

    if "plume" in layers:
        gx = np.linspace(0, SITE_SIZE, 140)
        GX, GY = np.meshgrid(gx, gx)
        field = gaussian_plume(GX, GY, ex, ey, eq, eu, etheta)
        fmax = float(np.max(field))
        if fmax > 0.5 * threshold:
            ax.contour(GX, GY, field, levels=[0.5 * threshold], colors=[CYAN], linestyles="--",
                       linewidths=0.9, alpha=0.85, zorder=3)
        if fmax > threshold:
            ax.contour(GX, GY, field, levels=[threshold], colors=[RED], linestyles="-",
                       linewidths=1.3, alpha=0.9, zorder=3)
        extra_handles.append(Line2D([0], [0], color=CYAN, lw=1.2, ls="--", label="Predicted 50% alarm contour"))
        extra_handles.append(Line2D([0], [0], color=RED, lw=1.6, label="Predicted alarm contour"))

    if "rings" in layers:
        for r in (10, 20, 30):
            ax.add_patch(Circle((ex, ey), r, fill=False, ec=GREEN, ls=(0, (2, 4)), lw=0.7, alpha=0.4, zorder=3))
            ax.text(ex + r * 0.72, ey + r * 0.72, f"{r} m", color=GREEN, alpha=0.6, fontsize=7, clip_on=True)

    if "box" in layers:
        x0, x1 = result.intervals["x_ci"]
        y0, y1 = result.intervals["y_ci"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=True, fc=(0.2, 0.83, 0.6, 0.05),
                               ec=GREEN, ls="--", lw=1.1, zorder=3))
        extra_handles.append(Line2D([0], [0], color=GREEN, lw=1.2, ls="--", label="95% credible box (X, Y)"))

    if "cloud" in layers:
        idx = np.random.default_rng(0).choice(len(result.weights), size=min(700, len(result.weights)),
                                              p=result.weights / np.sum(result.weights))
        ax.scatter(result.particles[idx, 0], result.particles[idx, 1], s=3, color="#e2e8f0", alpha=0.35, zorder=3)
        extra_handles.append(Line2D([0], [0], marker="o", color="none", markerfacecolor="#e2e8f0",
                                    markersize=4, label="Particle cloud"))

    for i, name in enumerate(SENSOR_NAMES):
        sx, sy = SENSOR_XY[i]
        r = float(readings[i])
        col = RED if r >= threshold else (AMBER if r >= 0.5 * threshold else CYAN)
        if i >= k:
            col = "#64748b"
        ax.scatter(sx, sy, s=900, color=col, alpha=0.08, zorder=4)
        ax.scatter(sx, sy, s=340, color=col, alpha=0.16, zorder=4)
        ax.add_patch(Circle((sx, sy), 3.0 + 6.0 * min(r / max(threshold, 1e-6), 2.0), fill=False, ec=col,
                            lw=1.0, alpha=0.7, zorder=4))
        ax.scatter(sx, sy, s=110, marker="s", color=col, edgecolors="white", linewidths=0.9, zorder=6)
        ax.text(sx, sy + 7.5, f"{name}  {r:.2f}", color="white", fontsize=8, ha="center", va="bottom",
                weight="bold", zorder=7,
                bbox=dict(boxstyle="round,pad=0.25", fc="#0b1220", ec=col, lw=0.8, alpha=0.85))
    extra_handles.append(Line2D([0], [0], marker="s", color="none", markerfacecolor=CYAN,
                                markeredgecolor="white", markersize=8, label="Sensor nodes"))

    if truth is not None:
        ax.scatter(truth[0], truth[1], marker="*", s=330, color=RED, edgecolors="white", linewidths=0.9,
                   zorder=9, label="Simulated source (truth)")
    ax.axhline(ey, color=GREEN, alpha=0.12, lw=0.8, zorder=2)
    ax.axvline(ex, color=GREEN, alpha=0.12, lw=0.8, zorder=2)
    ax.scatter(ex, ey, marker="X", s=190, color=GREEN, edgecolors="black", linewidths=0.9, zorder=10,
               label="Estimated source")
    if baseline_xy is not None and "baseline" in layers:
        ax.scatter(*baseline_xy, marker="s", s=130, facecolors="none", edgecolors="#e2e8f0", linewidths=1.6,
                   zorder=8, label="Strongest-sensor baseline")

    if mobile is not None:
        trail = mobile.get("trail", [])
        start = mobile.get("start")
        pts = ([tuple(start)] if start is not None else []) + [(x, y) for x, y, _ in trail]
        if mobile.get("route_to") is not None and pts:
            ax.plot([pts[-1][0], mobile["route_to"][0]], [pts[-1][1], mobile["route_to"][1]], color=AMBER,
                    lw=1.3, ls=(0, (3, 3)), alpha=0.9, zorder=8)
        if len(pts) > 1:
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color=AMBER, lw=1.8, zorder=8)
        for i, (x, y, r) in enumerate(trail, 1):
            ax.scatter(x, y, marker="o", s=75, color=AMBER, edgecolors="black", linewidths=0.8, zorder=9)
            ax.text(x + 2.0, y - 4.8, f"M{i}  {r:.2f}", color=AMBER, fontsize=7.5, weight="bold", zorder=9,
                    clip_on=True, bbox=dict(boxstyle="round,pad=0.15", fc="#0b1220", ec="none", alpha=0.75))
        if start is not None:
            ax.scatter(*start, marker="^", s=170, color=AMBER, edgecolors="white", linewidths=1.0, zorder=10,
                       label="Mobile sensor start")
            ax.text(start[0], start[1] - 7.0, "MOBILE", color=AMBER, fontsize=7.5, ha="center", weight="bold",
                    zorder=10, clip_on=True)

    if active_point is not None:
        ax.scatter(*active_point, marker="D", s=105, color=AMBER, edgecolors="black", linewidths=0.9,
                   zorder=9, label="Suggested next sample")
        ax.text(active_point[0], active_point[1] + 3.6, "NEXT SAMPLE", color=AMBER, fontsize=7.5, ha="center",
                va="bottom", weight="bold", zorder=9, clip_on=True,
                bbox=dict(boxstyle="round,pad=0.2", fc="#0b1220", ec="none", alpha=0.7))

    ax.annotate("", xy=(96, 94), xytext=(96, 85), arrowprops=dict(arrowstyle="-|>", color="#94a3b8", lw=1.2))
    ax.text(96, 95.5, "N", ha="center", va="bottom", color="#94a3b8", fontsize=9, weight="bold")
    ax.plot([72, 92], [4, 4], color="#94a3b8", lw=1.5)
    ax.text(82, 5.5, "20 m", color="#94a3b8", fontsize=7.5, ha="center")

    handles, _ = ax.get_legend_handles_labels()
    handles = extra_handles + handles
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=4, frameon=True,
              fontsize=8, facecolor="#0b1220", edgecolor="#2a3b57", labelcolor="#cbd5e1")
    fig.tight_layout()
    return fig


def draw_dispersion(truth_xy, q, u, wind_from, threshold, figsize=(8.0, 5.6)):
    gx = np.linspace(0, SITE_SIZE, 400)  # fine grid: the near-source plume is under 1 m wide
    GX, GY = np.meshgrid(gx, gx)
    field = gaussian_plume(GX, GY, truth_xy[0], truth_xy[1], q, u, wind_from)
    fig, ax = plt.subplots(figsize=figsize)
    style_map_axes(fig, ax)
    positive = field[field > 0]
    fmax = float(np.percentile(positive, 99.5)) if positive.size else 0.0
    if fmax > 0:
        levels = np.concatenate(([0.0], fmax * np.geomspace(1e-3, 1.0, 20)))
        ax.contourf(GX, GY, np.minimum(field, fmax), levels=levels, cmap=PLUME_CMAP, zorder=2)
        if float(np.max(field)) > threshold:
            ax.contour(GX, GY, field, levels=[threshold], colors=[RED], linewidths=1.2, zorder=3)
    ax.scatter(SENSOR_XY[:, 0], SENSOR_XY[:, 1], s=95, marker="s", color=CYAN, edgecolors="white",
               label="Sensors", zorder=6)
    ax.scatter(truth_xy[0], truth_xy[1], marker="*", s=260, color=RED, edgecolors="white",
               label="Simulated leak source", zorder=7)
    ax.set_title("Gaussian plume concentration field (log-scaled contours, relative model units)",
                 color="#e2e8f0", fontsize=9)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=2, fontsize=8, facecolor="#0b1220", edgecolor="#2a3b57", labelcolor="#cbd5e1")
    fig.tight_layout()
    return fig


def draw_info_map(grid, scores, active_point, truth_xy, result, figsize=(8.0, 5.6)):
    fig, ax = plt.subplots(figsize=figsize)
    style_map_axes(fig, ax)
    masked = np.ma.masked_invalid(np.sqrt(np.clip(scores, 0.0, None)))
    if masked.count() > 0 and float(masked.max()) > 0:
        ax.contourf(grid, grid, masked, levels=16, cmap=INFO_CMAP, zorder=2)
    ax.scatter(SENSOR_XY[:, 0], SENSOR_XY[:, 1], s=95, marker="s", color=CYAN, edgecolors="white",
               label="Sensors", zorder=6)
    ax.scatter(truth_xy[0], truth_xy[1], marker="*", s=240, color=RED, edgecolors="white",
               label="Simulated source (truth)", zorder=7)
    ax.scatter(result.mean[0], result.mean[1], marker="X", s=150, color=GREEN, edgecolors="black",
               label="Estimated source", zorder=8)
    ax.scatter(*active_point, marker="D", s=110, color=AMBER, edgecolors="black", label="Best next sample", zorder=9)
    ax.set_title("Active-sensing map: where a new reading would be most informative (brighter = more)",
                 color="#e2e8f0", fontsize=9)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=2, fontsize=8, facecolor="#0b1220", edgecolor="#2a3b57", labelcolor="#cbd5e1")
    fig.tight_layout()
    return fig


def draw_mission_chart(history, upto):
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6))
    steps = [h["step"] for h in history]
    errs = [h["error"] for h in history]
    widths = [h["ci_w"] for h in history]
    for ax in axes:
        style_generic_axes(fig, ax)
        ax.set_xlabel("Mobile samples taken")
        ax.set_xticks(steps)
    axes[0].plot(steps, errs, color=GREEN, lw=2, marker="o")
    axes[0].axvline(upto, color=AMBER, ls="--", lw=1)
    axes[0].set_ylabel("Localisation error (m)")
    axes[0].set_title("Error vs mobile samples", fontsize=10)
    axes[1].plot(steps, widths, color=CYAN, lw=2, marker="o")
    axes[1].axvline(upto, color=AMBER, ls="--", lw=1)
    axes[1].set_ylabel("Mean 95% interval width (m)")
    axes[1].set_title("Uncertainty vs mobile samples", fontsize=10)
    fig.tight_layout()
    return fig


def draw_mobile_bench(summary):
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    style_generic_axes(fig, ax)
    steps = np.arange(summary["steps"] + 1)
    colors = {"active": GREEN, "chase": ORANGE, "random": "#94a3b8"}
    names = {"active": "Active sensing", "chase": "Chase estimate", "random": "Random walk"}
    for p in ("random", "chase", "active"):
        ax.plot(steps, summary["curves"][p], color=colors[p], lw=2, marker="o", label=names[p])
    ax.axhline(summary["fixed_mean"], color="#e2e8f0", ls=":", lw=1.2, label="Fixed sensors only")
    ax.set_xticks(steps)
    ax.set_xlabel("Mobile samples taken")
    ax.set_ylabel("Mean localisation error (m)")
    ax.set_title("Mobile-sensor policies (lower is better)", fontsize=10)
    ax.legend(fontsize=8, facecolor="#0b1220", edgecolor="#2a3b57", labelcolor="#cbd5e1")
    fig.tight_layout()
    return fig


# --------------------------- Benchmark charts --------------------------------
def draw_bench_summary(m: dict):
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    style_generic_axes(fig, ax)
    labels = ["Mean", "Median", "P95"]
    bayes = [m["bayes_mean"], m["bayes_median"], m["bayes_p95"]]
    base = [m["baseline_mean"], m["baseline_median"], m["baseline_p95"]]
    xs = np.arange(len(labels))
    ax.bar(xs - 0.2, bayes, 0.38, color=GREEN, label="Bayesian particle estimate")
    ax.bar(xs + 0.2, base, 0.38, color="#64748b", label="Strongest-sensor baseline")
    ax.set_xticks(xs)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Localisation error (m)")
    ax.set_title("Error summary", fontsize=10)
    ax.legend(fontsize=8, facecolor="#0b1220", edgecolor="#2a3b57", labelcolor="#cbd5e1")
    fig.tight_layout()
    return fig


def draw_bench_cdf(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    style_generic_axes(fig, ax)
    for col, color, label in (("Bayesian Error (m)", GREEN, "Bayesian particle estimate"),
                              ("Strongest-Sensor Baseline Error (m)", "#94a3b8", "Strongest-sensor baseline")):
        v = np.sort(df[col].to_numpy(dtype=float))
        ax.step(v, np.arange(1, len(v) + 1) / len(v), where="post", color=color, lw=2, label=label)
    ax.set_xlabel("Localisation error (m)")
    ax.set_ylabel("Fraction of scenarios")
    ax.set_title("Error CDF (left/up is better)", fontsize=10)
    ax.set_ylim(0, 1.02)
    ax.legend(fontsize=8, loc="lower right", facecolor="#0b1220", edgecolor="#2a3b57", labelcolor="#cbd5e1")
    fig.tight_layout()
    return fig


def draw_bench_coverage(m: dict):
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    style_generic_axes(fig, ax)
    vals = [100 * m["x_coverage"], 100 * m["y_coverage"], 100 * m["joint_coverage"]]
    bars = ax.bar(["X marginal", "Y marginal", "Joint X/Y"], vals, color=[CYAN, CYAN, ORANGE], width=0.55)
    ax.axhline(95, color=AMBER, ls="--", lw=1.2, label="95% nominal (per marginal)")
    ax.set_ylim(0, 105)
    ax.set_ylabel("Empirical coverage (%)")
    ax.set_title("Credible-interval coverage", fontsize=10)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}%", ha="center", color="#e2e8f0", fontsize=8)
    ax.legend(fontsize=8, loc="lower right", facecolor="#0b1220", edgecolor="#2a3b57", labelcolor="#cbd5e1")
    fig.tight_layout()
    return fig
