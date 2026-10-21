"""Alert / banner logic and the change event log."""

from __future__ import annotations

import math
import numpy as np
import streamlit as st
import time

from .config import EDGE_LATENCY_TARGET_MS, SENSOR_NAMES, SENSOR_XY
from .inference import InferenceResult
from .ui import cardinal, level_of


# ------------------------------- Alerts --------------------------------------
def posterior_confidence(result: InferenceResult, radius: float = 12.0) -> float:
    d = np.hypot(result.particles[:, 0] - result.mean[0], result.particles[:, 1] - result.mean[1])
    return float(np.sum(result.weights[d < radius]))


def build_alerts(readings, k, threshold, result: InferenceResult, latency_ms, mobile_point=None):
    """Return (headline, items). headline=(kind, title, sub). items=[(kind, title, detail)]."""
    ex, ey, eq, eu, eth = result.mean
    peak_i = int(np.argmax(readings))
    peak = float(readings[peak_i])
    conf = posterior_confidence(result)
    radius = max(0.5 * (result.intervals["x_ci"][1] - result.intervals["x_ci"][0]),
                 0.5 * (result.intervals["y_ci"][1] - result.intervals["y_ci"][0]))
    items = []
    if peak >= threshold:
        head = ("red", "🚨 SENSOR LEAK PREDICTED",
                f"Strongest: {SENSOR_NAMES[peak_i]} ({peak:.2f}) · source ≈ ({ex:.1f}, {ey:.1f}) m ± {radius:.0f} m · "
                f"confidence {100 * conf:.0f}% · Q̂ {eq:.0f}")
        items.append(("red", "LEAK PREDICTED", f"Source ≈ ({ex:.1f}, {ey:.1f}) m (±{radius:.0f} m), confidence {100 * conf:.0f}%."))
    elif peak >= 0.5 * threshold:
        head = ("amber", "⚠ ELEVATED CONCENTRATION · MONITORING",
                f"{SENSOR_NAMES[peak_i]} reads {peak:.2f} (warn ≥ {0.5 * threshold:.2f}, alarm ≥ {threshold:.2f})")
        items.append(("amber", "ELEVATED", f"{SENSOR_NAMES[peak_i]} above warning level; leak not confirmed."))
    else:
        head = ("green", "✔ NO LEAK PREDICTED", f"All nodes below warning level · peak {peak:.2f} < {0.5 * threshold:.2f}")
        items.append(("green", "ALL CLEAR", "No node above warning level."))
    for i, name in enumerate(SENSOR_NAMES):
        cls, label = level_of(float(readings[i]), threshold)
        d = float(np.hypot(SENSOR_XY[i, 0] - ex, SENSOR_XY[i, 1] - ey))
        state = "assimilated" if i < k else "queued"
        items.append((cls if cls != "green" else "blue", f"{name} · {label}",
                      f"{readings[i]:.3f} · {d:.0f} m from estimated source · {state}"))
    if peak >= 0.5 * threshold:
        items.append(("blue", "DISPATCH / INSPECT",
                      f"Inspect zone centred ({ex:.0f}, {ey:.0f}) m, radius {max(radius, 5):.0f} m. Approach from upwind "
                      f"({cardinal(eth)}, {eth:.0f}°)."))
    if result.ess < 15:
        items.append(("amber", "LOW PARTICLE DIVERSITY", f"ESS {result.ess:.0f}; raise particle count."))
    if latency_ms >= EDGE_LATENCY_TARGET_MS:
        items.append(("amber", "LATENCY", f"{latency_ms:.0f} ms (edge target {EDGE_LATENCY_TARGET_MS:.0f} ms, budget 2 s)."))
    if mobile_point is not None:
        items.append(("blue", "MOBILE SENSOR", f"Next suggested sample at ({mobile_point[0]:.0f}, {mobile_point[1]:.0f}) m."))
    return head, items


def alerts_html(items) -> str:
    return "".join(f"<div class='alert {k}'><b>{t}</b><br>{d}</div>" for k, t, d in items)


PARAM_LABELS = {
    "leak_x": "Leak X", "leak_y": "Leak Y", "strength": "Release Q", "wind_speed": "Wind speed",
    "wind_from": "Wind FROM", "alarm_threshold": "Alarm threshold", "measurement_noise": "Sensor noise",
    "k_assim": "Readings assimilated", "mob_start_x": "Mobile start X", "mob_start_y": "Mobile start Y",
    "mob_steps": "Mobile samples", "mob_policy": "Mobile policy", "n_particles": "Particles",
}


def update_event_log(params: dict, levels: dict, pred: bool, est_xy) -> list:
    """Compare against the previous run and log what changed (kept in session_state)."""
    ss = st.session_state
    log = ss.setdefault("event_log", [])
    now = time.strftime("%H:%M:%S")
    prev = ss.get("prev_params")
    if prev is not None:
        for key, label in PARAM_LABELS.items():
            if prev.get(key) != params.get(key):
                log.append((now, "blue", f"{label}: {prev.get(key)} → {params.get(key)}"))
    prev_levels = ss.get("prev_levels")
    if prev_levels is not None:
        for name, lv in levels.items():
            old = prev_levels.get(name)
            if old is not None and old != lv:
                log.append((now, "red" if lv == "ALARM" else ("amber" if lv == "WARN" else "green"),
                            f"{name}: {old} → {lv}"))
    prev_pred = ss.get("prev_pred")
    if prev_pred is not None and prev_pred != pred:
        log.append((now, "red" if pred else "green", "LEAK PREDICTED" if pred else "Leak prediction cleared"))
    prev_est = ss.get("prev_est")
    if prev_est is not None and math.hypot(est_xy[0] - prev_est[0], est_xy[1] - prev_est[1]) > 5.0:
        log.append((now, "blue", f"Estimated source moved to ({est_xy[0]:.1f}, {est_xy[1]:.1f}) m"))
    ss["prev_params"], ss["prev_levels"], ss["prev_pred"], ss["prev_est"] = params, levels, pred, est_xy
    del log[:-30]
    return log
