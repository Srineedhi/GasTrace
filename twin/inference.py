"""Particle-filter (SMC) source inference and active-sensing heuristic."""

from __future__ import annotations

import math
import numpy as np
from dataclasses import dataclass

from .config import SITE_SIZE
from .physics import circular_difference_deg, gaussian_plume


@dataclass
class InferenceResult:
    particles: np.ndarray
    weights: np.ndarray
    mean: np.ndarray
    intervals: dict[str, tuple[float, float]]
    ess: float
    resampled: bool

def weighted_quantile(values, weights, quantiles):
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    quantiles = np.atleast_1d(np.asarray(quantiles, dtype=float))
    order = np.argsort(values)
    vals, w = values[order], weights[order]
    cumulative = np.cumsum(w)
    if len(cumulative) == 0 or cumulative[-1] <= 0:
        return np.quantile(values, quantiles)
    cumulative /= cumulative[-1]
    return np.interp(quantiles, cumulative, vals)


def weighted_circular_mean_deg(angles, weights):
    angles = np.radians(np.asarray(angles, dtype=float))
    s = np.sum(weights * np.sin(angles))
    c = np.sum(weights * np.cos(angles))
    return float(np.degrees(np.arctan2(s, c)) % 360.0)


def make_prior_particles(n, wind_speed_obs, wind_from_obs, wind_speed_sd,
                         wind_dir_sd, rng):
    return np.column_stack((
        rng.uniform(0.0, SITE_SIZE, n),                 # source X
        rng.uniform(0.0, SITE_SIZE, n),                 # source Y
        rng.uniform(10.0, 100.0, n),                   # release Q (relative)
        np.clip(rng.normal(wind_speed_obs, wind_speed_sd, n), 0.5, 12.0),
        (wind_from_obs + rng.normal(0.0, wind_dir_sd, n)) % 360.0,
    ))


def particle_filter_frame(sensor_coords, observed, wind_speed_obs, wind_from_obs,
                          n_particles=4000, noise_std=0.4, wind_speed_sd=1.0,
                          wind_dir_sd=25.0, seed=123, offsets=None,
                          resample_threshold=0.45):
    """
    Sequential Monte Carlo update across the sensor readings in one frame.
    Each sensor observation (fixed OR mobile) updates the particle weights once;
    low ESS triggers systematic resampling. The returned cloud is an approximate posterior.
    """
    rng = np.random.default_rng(seed)
    n = int(n_particles)
    particles = make_prior_particles(
        n, float(wind_speed_obs), float(wind_from_obs),
        max(float(wind_speed_sd), 0.05), max(float(wind_dir_sd), 1.0), rng
    )
    weights = np.full(n, 1.0 / n, dtype=float)
    sigma = max(float(noise_std), 1e-3)
    did_resample = False

    for i, (sx, sy) in enumerate(sensor_coords):
        predicted = gaussian_plume(
            sx, sy, particles[:, 0], particles[:, 1], particles[:, 2],
            particles[:, 3], particles[:, 4]
        )
        if offsets is not None:
            predicted = predicted + float(offsets[i])
        residual = (float(observed[i]) - predicted) / sigma
        log_likelihood = -0.5 * residual**2 - math.log(sigma * math.sqrt(2.0 * math.pi))
        log_likelihood -= np.max(log_likelihood)
        likelihood = np.exp(log_likelihood)
        weights *= likelihood
        total = float(np.sum(weights))
        if not np.isfinite(total) or total <= 1e-300:
            weights.fill(1.0 / n)
        else:
            weights /= total

        ess = 1.0 / float(np.sum(weights**2))
        if ess < resample_threshold * n and i < len(sensor_coords) - 1:
            positions = (rng.random() + np.arange(n)) / n
            cumulative = np.cumsum(weights)
            indexes = np.searchsorted(cumulative, positions, side="left")
            particles = particles[np.minimum(indexes, n - 1)]
            weights.fill(1.0 / n)
            did_resample = True

    ess = 1.0 / float(np.sum(weights**2))
    mean = np.sum(particles * weights[:, None], axis=0)
    mean[4] = weighted_circular_mean_deg(particles[:, 4], weights)
    intervals = {
        "x_ci": tuple(weighted_quantile(particles[:, 0], weights, [0.025, 0.975])),
        "y_ci": tuple(weighted_quantile(particles[:, 1], weights, [0.025, 0.975])),
        "q_ci": tuple(weighted_quantile(particles[:, 2], weights, [0.025, 0.975])),
        "u_ci": tuple(weighted_quantile(particles[:, 3], weights, [0.025, 0.975])),
    }
    delta = circular_difference_deg(particles[:, 4], mean[4])
    delta_ci = weighted_quantile(delta, weights, [0.025, 0.975])
    intervals["theta_ci"] = (
        float((mean[4] + delta_ci[0]) % 360.0),
        float((mean[4] + delta_ci[1]) % 360.0),
    )
    return InferenceResult(particles, weights, mean, intervals, ess, did_resample)


def nearest_sensor_baseline(sensor_coords, observed, true_x, true_y):
    """Baseline: estimate the leak at the location of the strongest-reading sensor."""
    idx = int(np.argmax(observed))
    bx, by = sensor_coords[idx]
    return float(np.hypot(bx - true_x, by - true_y)), (float(bx), float(by))


def active_sensing_scores(result, sensor_coords, noise_std=0.4, grid_res=21, max_particles=1000,
                          origin=None, max_step=None, min_sep=6.0):
    """
    Information-seeking heuristic: posterior predictive variance / noise variance
    on a candidate grid. Not a formal expected-information-gain solution and not
    flight-safe routing.

    sensor_coords : every point that already has a sensor (fixed + visited mobile points);
                    candidates closer than `min_sep` to any of them are masked out.
    origin/max_step : optional reachability limit for the mobile sensor (candidates farther
                    than max_step from `origin` are masked out).
    Returns (grid, score_matrix, best_point, best_score).
    """
    grid = np.linspace(5.0, 95.0, int(grid_res))
    GX, GY = np.meshgrid(grid, grid)
    stride = max(1, len(result.weights) // max_particles)
    p = result.particles[::stride]
    w = result.weights[::stride]
    w = w / np.sum(w)
    pred = gaussian_plume(GX[..., None], GY[..., None], p[:, 0], p[:, 1], p[:, 2], p[:, 3], p[:, 4])
    mean_pred = np.sum(pred * w, axis=-1)
    variance = np.sum(w * (pred - mean_pred[..., None]) ** 2, axis=-1)
    score = variance / (float(noise_std) ** 2 + 1e-9)
    coords = np.asarray(sensor_coords, dtype=float).reshape(-1, 2)
    dist = np.min(np.hypot(coords[:, 0, None, None] - GX, coords[:, 1, None, None] - GY), axis=0)
    score = np.where(dist < min_sep, np.nan, score)
    if origin is not None and max_step is not None:
        reach = np.hypot(GX - origin[0], GY - origin[1]) <= float(max_step)
        score = np.where(reach, score, np.nan)
    if np.all(np.isnan(score)):
        fallback = (float(origin[0]), float(origin[1])) if origin is not None else (50.0, 50.0)
        return grid, score, fallback, 0.0
    iy, ix = np.unravel_index(int(np.nanargmax(score)), score.shape)
    return grid, score, (float(grid[ix]), float(grid[iy])), float(score[iy, ix])


def recommend_active_sensing(result, sensor_coords, noise_std=0.4, grid_res=13):
    """Backward-compatible wrapper returning (best_point, best_score)."""
    _, _, point, score = active_sensing_scores(result, sensor_coords, noise_std, grid_res)
    return point, score
