"""HTML panels: SCADA table, wind compass, credible intervals, gauges."""

from __future__ import annotations

import math
import numpy as np

from .config import AMBER, CYAN, EDGE_LATENCY_TARGET_MS, GREEN, HARD_LATENCY_BUDGET_MS, RED, SENSOR_NAMES, SENSOR_OFFSETS, SENSOR_XY, SITE_SIZE
from .inference import InferenceResult
from .physics import circular_difference_deg
from .ui import cardinal, level_of, wind_label


# ------------------------------ HTML panels ----------------------------------
def scada_panel(readings, k: int, threshold: float, truth_xy) -> str:
    rows = []
    for i, name in enumerate(SENSOR_NAMES):
        r = float(readings[i])
        sx, sy = SENSOR_XY[i]
        cls, label = level_of(r, threshold)
        frac = min(r / (1.5 * max(threshold, 1e-6)), 1.0)
        ingest, icls = ("INGESTED", "blue") if i < k else ("QUEUED", "gray")
        dist = float(np.hypot(sx - truth_xy[0], sy - truth_xy[1]))
        rows.append(
            f"<tr><td><div class='mono' style='font-weight:700;color:#f1f5f9'>{name}</div>"
            f"<div class='sub mono'>({sx:.0f}, {sy:.0f}) m</div></td>"
            f"<td><div class='mono' style='font-size:.95rem'>{r:.3f}</div>"
            f"<div class='sub mono'>bias {SENSOR_OFFSETS[i]:+.2f}</div></td>"
            f"<td style='width:30%'><div class='bar'><div class='fill {cls}' style='width:{frac * 100:.0f}%'></div></div>"
            f"<div class='sub mono'>Δ truth {dist:.0f} m</div></td>"
            f"<td><span class='chip {cls}'>{label}</span>"
            f"<div style='margin-top:.25rem'><span class='chip {icls}'>{ingest}</span></div></td></tr>"
        )
    peak, mean = float(np.max(readings)), float(np.mean(readings))
    return (
        "<div class='panel'><div class='panel-head'><span class='panel-title'>LIVE SCADA TELEMETRY</span>"
        "<span class='tag live'>● STREAMING</span></div>"
        "<table class='scada'><thead><tr><th>NODE</th><th>READING*</th><th>LEVEL</th><th>STATUS</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        f"<div class='sub' style='margin-top:.7rem'>*Synthetic model units · alarm threshold {threshold:.2f} · "
        f"peak {peak:.3f} · mean {mean:.3f}. Δ truth is evaluation-only.</div></div>"
    )


def compass_svg(true_from, obs_from, obs_speed, true_speed, est_from, est_speed, theta_ci, size=250) -> str:
    cx = cy = size / 2.0
    R = size / 2.0 - 26.0

    def pt(deg, r):
        a = math.radians(deg)
        return cx + r * math.sin(a), cy - r * math.cos(a)

    markers = "".join(
        f"<marker id='{mid}' markerUnits='userSpaceOnUse' markerWidth='12' markerHeight='12' refX='9' refY='6' "
        f"orient='auto'><path d='M0,1 L11,6 L0,11 z' fill='{col}'/></marker>"
        for mid, col in (("mkC", CYAN), ("mkG", GREEN), ("mkW", "#f8fafc"))
    )
    s = [
        f"<svg viewBox='0 0 {size} {size}' width='{size}' height='{size}' xmlns='http://www.w3.org/2000/svg'>",
        "<defs><radialGradient id='cg' cx='50%' cy='50%' r='60%'><stop offset='0%' stop-color='#13243f'/>"
        "<stop offset='100%' stop-color='#0a1220'/></radialGradient>"
        "<filter id='gl' x='-30%' y='-30%' width='160%' height='160%'><feGaussianBlur stdDeviation='2.2' result='b'/>"
        f"<feMerge><feMergeNode in='b'/><feMergeNode in='SourceGraphic'/></feMerge></filter>{markers}</defs>",
        f"<circle cx='{cx}' cy='{cy}' r='{R + 9}' fill='url(#cg)' stroke='#28405f' stroke-width='1.5'/>",
    ]
    for frac in (1.0, 0.66, 0.33):
        s.append(f"<circle cx='{cx}' cy='{cy}' r='{R * frac:.1f}' fill='none' stroke='#1f3354' stroke-width='1'/>")
    for deg in range(0, 360, 10):
        length = 10 if deg % 90 == 0 else (6 if deg % 30 == 0 else 3)
        x0, y0 = pt(deg, R)
        x1, y1 = pt(deg, R - length)
        col = "#7dd3fc" if deg % 90 == 0 else "#3b5378"
        s.append(f"<line x1='{x0:.1f}' y1='{y0:.1f}' x2='{x1:.1f}' y2='{y1:.1f}' stroke='{col}' stroke-width='1'/>")
    for deg, lab in ((0, "N"), (90, "E"), (180, "S"), (270, "W")):
        x, y = pt(deg, R + 17)
        col = "#fda4af" if lab == "N" else "#9fb0c8"
        s.append(f"<text x='{x:.1f}' y='{y:.1f}' fill='{col}' font-size='11' font-weight='700' text-anchor='middle' "
                 f"dominant-baseline='central' font-family='JetBrains Mono, monospace'>{lab}</text>")

    lo_from, hi_from = theta_ci
    span = (hi_from - lo_from) % 360.0
    if span >= 359.0:
        s.append(f"<circle cx='{cx}' cy='{cy}' r='{R:.1f}' fill='rgba(52,211,153,.12)'/>")
    elif span > 0.5:
        a0 = (lo_from + 180.0) % 360.0
        p0, p1 = pt(a0, R), pt(a0 + span, R)
        large = 1 if span > 180.0 else 0
        s.append(f"<path d='M{cx},{cy} L{p0[0]:.1f},{p0[1]:.1f} A{R:.1f},{R:.1f} 0 {large} 1 {p1[0]:.1f},{p1[1]:.1f} Z' "
                 "fill='rgba(52,211,153,.16)' stroke='rgba(52,211,153,.5)' stroke-width='1' stroke-dasharray='3 3'/>")

    def arrow(frm, speed, col, mk, width, dash="", glow=True):
        toward = (frm + 180.0) % 360.0
        length = min(R * 0.92, R * 0.28 + R * 0.075 * float(speed))
        x0, y0 = pt(frm, length / 2.0)
        x1, y1 = pt(toward, length / 2.0)
        extra = " filter='url(#gl)'" if glow else ""
        dash_attr = f" stroke-dasharray='{dash}'" if dash else ""
        s.append(f"<line x1='{x0:.1f}' y1='{y0:.1f}' x2='{x1:.1f}' y2='{y1:.1f}' stroke='{col}' "
                 f"stroke-width='{width}' stroke-linecap='round' marker-end='url(#{mk})'{dash_attr}{extra}/>")

    arrow(true_from, true_speed, "#f8fafc", "mkW", 1.6, dash="4 4", glow=False)
    arrow(obs_from, obs_speed, CYAN, "mkC", 2.4)
    arrow(est_from, est_speed, GREEN, "mkG", 3.2)
    for frm, col in ((obs_from, CYAN), (est_from, GREEN)):
        x, y = pt(frm, R)
        s.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='3.6' fill='{col}' stroke='#0b1220' stroke-width='1'/>")
    s.append(f"<circle cx='{cx}' cy='{cy}' r='4.5' fill='#0b1220' stroke='{CYAN}' stroke-width='1.5'/>")
    s.append("</svg>")
    return "".join(s)


def wind_panel(true_u, true_dir, obs_u, obs_dir, result: InferenceResult, sd_u, sd_dir) -> str:
    _, _, _, eu, eth = result.mean
    u_lo, u_hi = result.intervals["u_ci"]
    th_lo, th_hi = result.intervals["theta_ci"]
    half = ((th_hi - th_lo) % 360.0) / 2.0
    svg = compass_svg(true_dir, obs_dir, obs_u, true_u, eth, eu, result.intervals["theta_ci"])
    down = (eth + 180.0) % 360.0
    stats = [
        ("TELEMETRY (NOISY)", f"{obs_u:.1f} m/s · {obs_dir:.0f}° {cardinal(obs_dir)}", f"σ {sd_u:.1f} m/s · {sd_dir:.0f}°"),
        ("ESTIMATED (POSTERIOR)", f"{eu:.2f} m/s · {eth:.0f}° {cardinal(eth)}", f"95%: ±{half:.0f}° · {u_lo:.1f}–{u_hi:.1f} m/s"),
        ("TRUE WIND (SIM)", f"{true_u:.1f} m/s · {true_dir:.0f}° {cardinal(true_dir)}", wind_label(true_u)),
        ("DOWNWIND BEARING", f"{down:.0f}° {cardinal(down)}", wind_label(eu)),
    ]
    cells = "".join(
        f"<div class='stat'><div class='stat-label'>{a}</div><div class='stat-value mono'>{b}</div>"
        f"<div class='sub mono'>{c}</div></div>" for a, b, c in stats
    )
    legend = (
        f"<span><span class='ldot' style='background:{GREEN}'></span>Estimated</span>"
        f"<span><span class='ldot' style='background:{CYAN}'></span>Telemetry</span>"
        "<span><span class='ldot' style='background:#f8fafc'></span>True (sim)</span>"
    )
    return (
        "<div class='panel'><div class='panel-head'><span class='panel-title'>ENVIRONMENT · WIND VECTORS</span>"
        "<span class='tag sim'>WIND FROM → FLOW TO</span></div>"
        f"<div class='wind-wrap'>{svg}</div><div class='legend-row'>{legend}</div>"
        f"<div class='stat-grid'>{cells}</div></div>"
    )


def interval_card(label, est, ci, dom, unit, truth, digits=1) -> str:
    lo, hi = ci
    d0, d1 = dom

    def pos(v):
        return float(np.clip((v - d0) / (d1 - d0), 0.0, 1.0)) * 100.0

    left = pos(lo)
    width = max(pos(hi) - left, 1.2)
    covered = lo <= truth <= hi
    mark = ("<span style='color:#34d399'>✓ covers truth</span>" if covered
            else "<span style='color:#fb7185'>✗ misses truth</span>")
    return (
        f"<div class='ci'><div class='ci-top'><span class='ci-label'>{label}</span>"
        f"<span class='ci-est mono'>{est:.{digits}f} {unit}</span></div>"
        f"<div class='ci-track'><div class='ci-band' style='left:{left:.1f}%;width:{width:.1f}%'></div>"
        f"<div class='ci-tick' style='left:{pos(est):.1f}%'></div>"
        f"<div class='ci-truth' style='left:{pos(truth):.1f}%'></div></div>"
        f"<div class='ci-foot mono'><span>95% [{lo:.{digits}f}, {hi:.{digits}f}]</span>{mark}</div></div>"
    )


def direction_card(est, ci, true_from) -> str:
    lo, hi = ci
    half = ((hi - lo) % 360.0) / 2.0
    d_lo = float(circular_difference_deg(lo, est))
    d_hi = float(circular_difference_deg(hi, est))
    d_t = float(circular_difference_deg(true_from, est))
    covered = d_lo <= d_t <= d_hi
    mark = ("<span style='color:#34d399'>✓ covers truth</span>" if covered
            else "<span style='color:#fb7185'>✗ misses truth</span>")
    return (
        "<div class='ci'><div class='ci-top'><span class='ci-label'>WIND FROM (CIRCULAR)</span>"
        f"<span class='ci-est mono'>{est:.0f}° {cardinal(est)}</span></div>"
        f"<div class='ci-foot mono' style='margin-top:.45rem'><span>95% ±{half:.0f}° [{lo:.0f}°, {hi:.0f}°]</span>{mark}</div></div>"
    )


def gauge_svg(frac, value_text, label, color) -> str:
    r, cx, cy = 42.0, 60.0, 56.0
    frac = float(np.clip(frac, 0.0, 1.0))

    def pt(f):
        a = math.pi * f
        return cx - r * math.cos(a), cy - r * math.sin(a)

    x0, y0 = pt(0.0)
    x1, y1 = pt(1.0)
    track = f"<path d='M{x0:.1f},{y0:.1f} A{r},{r} 0 0 1 {x1:.1f},{y1:.1f}' fill='none' stroke='#1b2a44' stroke-width='9' stroke-linecap='round'/>"
    val = ""
    if frac > 0.005:
        xe, ye = pt(frac)
        val = (f"<path d='M{x0:.1f},{y0:.1f} A{r},{r} 0 0 1 {xe:.1f},{ye:.1f}' fill='none' stroke='{color}' "
               f"stroke-width='9' stroke-linecap='round' style='filter:drop-shadow(0 0 4px {color})'/>")
    return (
        "<svg viewBox='0 0 120 82' width='100%' xmlns='http://www.w3.org/2000/svg'>"
        f"{track}{val}"
        f"<text x='60' y='54' fill='#f1f5f9' font-size='13' font-weight='700' text-anchor='middle' "
        f"font-family='JetBrains Mono, monospace'>{value_text}</text>"
        f"<text x='60' y='74' fill='#8b9ab3' font-size='7.5' text-anchor='middle' font-weight='700' "
        f"letter-spacing='.6'>{label}</text></svg>"
    )


def ci_panel(result: InferenceResult, truth, latency_ms: float) -> str:
    ex, ey, eq, eu, eth = result.mean
    t_x, t_y, t_q, t_u, t_dir = truth
    cards = "".join([
        interval_card("SOURCE X", ex, result.intervals["x_ci"], (0, SITE_SIZE), "m", t_x),
        interval_card("SOURCE Y", ey, result.intervals["y_ci"], (0, SITE_SIZE), "m", t_y),
        interval_card("RELEASE RATE Q", eq, result.intervals["q_ci"], (10, 100), "rel", t_q),
        interval_card("WIND SPEED", eu, result.intervals["u_ci"], (0.5, 12.0), "m/s", t_u, digits=2),
        direction_card(eth, result.intervals["theta_ci"], t_dir),
    ])
    lat_col = GREEN if latency_ms < EDGE_LATENCY_TARGET_MS else (AMBER if latency_ms < HARD_LATENCY_BUDGET_MS else RED)
    ess_col = GREEN if result.ess >= 50 else (AMBER if result.ess >= 15 else RED)
    width = 0.5 * ((result.intervals["x_ci"][1] - result.intervals["x_ci"][0]) +
                   (result.intervals["y_ci"][1] - result.intervals["y_ci"][0]))
    sp_col = GREEN if width < 25 else (AMBER if width < 50 else RED)
    gauges = (
        f"<div class='gauge'>{gauge_svg(latency_ms / 100.0, f'{latency_ms:.0f} ms', 'LATENCY (0-100 ms)', lat_col)}</div>"
        f"<div class='gauge'>{gauge_svg(result.ess / len(result.weights), f'{result.ess:.0f}', 'ESS (OF N)', ess_col)}</div>"
        f"<div class='gauge'>{gauge_svg(width / SITE_SIZE, f'{width:.0f} m', '95% CI WIDTH', sp_col)}</div>"
    )
    return (
        "<div class='panel'><div class='panel-head'><span class='panel-title'>POSTERIOR · 95% CREDIBLE INTERVALS</span>"
        "<span class='tag live'>SMC</span></div>"
        f"{cards}"
        "<div class='sub' style='margin:.1rem 0 .3rem'>◇ marks simulated truth (evaluation-only). Green tick = posterior mean.</div>"
        f"<div class='gauge-row'>{gauges}</div></div>"
    )
