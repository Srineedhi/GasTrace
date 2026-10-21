"""Site layout, sensor positions, palette and shared constants."""

from __future__ import annotations

import numpy as np


# ------------------------------- Palette -------------------------------------
MAP_BG = "#0e1726"
CYAN = "#38bdf8"
ORANGE = "#fb923c"
GREEN = "#34d399"
RED = "#f43f5e"
AMBER = "#fbbf24"
MUTED = "#8b9ab3"

# ----------------------------- Site definition -------------------------------
SITE_SIZE = 100.0
SENSORS = {
    "S1": (10.0, 10.0),
    "S2": (10.0, 80.0),
    "S3": (80.0, 10.0),
    "S4": (80.0, 80.0),
}
SENSOR_NAMES = list(SENSORS)
SENSOR_XY = np.asarray([SENSORS[n] for n in SENSOR_NAMES], dtype=float)
# Illustrative sensor bias, used consistently by simulation and inference.
SENSOR_OFFSETS = np.array([-0.15, 0.10, -0.08, 0.12], dtype=float)
MOBILE_OFFSET = 0.05  # bias of the mobile sensor (model units)
N_SENSORS = len(SENSOR_NAMES)

EDGE_LATENCY_TARGET_MS = 50.0
HARD_LATENCY_BUDGET_MS = 2000.0

POLICY_LABELS = {
    "active": "Active sensing (recommended)",
    "chase": "Chase the estimate",
    "random": "Random walk",
}
