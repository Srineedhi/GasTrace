"""Gaussian-plume forward model and synthetic sensor readings."""

from __future__ import annotations

import numpy as np


# ------------------------------ Physics & inference --------------------------
def circular_difference_deg(a, b):
    """Shortest signed angular difference a-b, in degrees."""
    return (np.asarray(a) - np.asarray(b) + 180.0) % 360.0 - 180.0


def gaussian_plume(x_sensor, y_sensor, x_src, y_src, q, wind_speed,
                   wind_from_deg, source_height=1.0):
    """
    Simplified ground-level Gaussian plume approximation.

    Coordinates: X east, Y north. wind_from_deg is meteorological direction
    clockwise from north indicating where wind comes FROM. Q and concentration
    are relative model units; calibration is required for physical units.
    """
    u = np.maximum(np.asarray(wind_speed, dtype=float), 0.1)
    theta = np.radians(np.asarray(wind_from_deg, dtype=float) % 360.0)
    dx = np.asarray(x_sensor, dtype=float) - np.asarray(x_src, dtype=float)
    dy = np.asarray(y_sensor, dtype=float) - np.asarray(y_src, dtype=float)

    x_down = -dx * np.sin(theta) - dy * np.cos(theta)
    y_cross = dx * np.cos(theta) - dy * np.sin(theta)
    x_eff = np.maximum(x_down, 0.1)

    sigma_y = np.maximum(0.08 * x_eff / np.sqrt(1.0 + 0.0001 * x_eff), 0.25)
    sigma_z = np.maximum(0.06 * x_eff / np.sqrt(1.0 + 0.0015 * x_eff), 0.25)
    h = max(float(source_height), 0.0)
    vertical = 2.0 * np.exp(-0.5 * (h / sigma_z) ** 2)

    concentration = (
        np.asarray(q, dtype=float)
        / (2.0 * np.pi * u * sigma_y * sigma_z)
        * np.exp(-0.5 * (y_cross / sigma_y) ** 2)
        * vertical
    )
    return np.where(x_down > 0.1, concentration, 0.0)


def simulate_readings(source_x, source_y, q, wind_speed, wind_from_deg,
                      sensor_coords, rng, noise_std=0.2, offsets=None):
    expected = gaussian_plume(
        sensor_coords[:, 0], sensor_coords[:, 1], source_x, source_y,
        q, wind_speed, wind_from_deg
    )
    if offsets is not None:
        expected = expected + np.asarray(offsets, dtype=float)
    return np.maximum(expected + rng.normal(0.0, noise_std, len(sensor_coords)), 0.0)
