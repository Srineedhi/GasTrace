"""Closed-loop mobile-sensor mission and the offline benchmarks."""

from __future__ import annotations

import math
import numpy as np
import pandas as pd
import time

from .config import HARD_LATENCY_BUDGET_MS, MOBILE_OFFSET, SENSOR_OFFSETS, SENSOR_XY
from .inference import active_sensing_scores, nearest_sensor_baseline, particle_filter_frame
from .physics import simulate_readings


# ------------------------------ Mobile sensing mission -----------------------
def run_mobile_mission(truth, fixed_obs, wind_obs, wind_sd, start, steps, max_step, policy,
                       n_particles, noise_std, seed, grid_res=17):
    """
    Closed-loop mobile-sensor mission:
        step 0 : posterior from the fixed sensors only
        step k : choose next waypoint (policy) -> move (<= max_step m) -> take a noisy reading
                 -> assimilate it with the fixed readings -> new posterior.
    policy: "active" (posterior-predictive variance), "chase" (head to current estimate),
            "random" (random move) or "fixed" (never moves).
    Every step records measured wall-clock time (waypoint selection + inference), which is the
    'update per new reading' latency.
    """
    tx, ty, tq, tu, tdir = truth
    rng_meas = np.random.default_rng(seed)
    rng_move = np.random.default_rng(seed + 7)
    pos = np.array(start, dtype=float)
    mob_xy: list[tuple[float, float]] = []
    mob_obs: list[float] = []
    history: list[dict] = []

    def infer():
        if mob_xy:
            coords = np.vstack([SENSOR_XY, np.array(mob_xy)])
            obs = np.concatenate([np.asarray(fixed_obs, float), np.array(mob_obs)])
            offs = np.concatenate([SENSOR_OFFSETS, np.full(len(mob_xy), MOBILE_OFFSET)])
        else:
            coords, obs, offs = SENSOR_XY, np.asarray(fixed_obs, float), SENSOR_OFFSETS
        res = particle_filter_frame(
            coords, obs, wind_obs[0], wind_obs[1], n_particles=n_particles, noise_std=noise_std,
            wind_speed_sd=wind_sd[0], wind_dir_sd=wind_sd[1], seed=seed + 1, offsets=offs
        )
        return res, coords

    def record(step, res, coords, ms, reading):
        w = 0.5 * ((res.intervals["x_ci"][1] - res.intervals["x_ci"][0]) +
                   (res.intervals["y_ci"][1] - res.intervals["y_ci"][0]))
        history.append({
            "step": step, "pos": (float(pos[0]), float(pos[1])), "reading": reading, "result": res,
            "coords": coords, "error": float(np.hypot(res.mean[0] - tx, res.mean[1] - ty)),
            "ci_w": float(w), "ess": float(res.ess), "latency_ms": float(ms),
        })

    t0 = time.perf_counter()
    res, coords = infer()
    record(0, res, coords, (time.perf_counter() - t0) * 1000.0, None)
    if policy == "fixed":
        return history

    for s in range(1, int(steps) + 1):
        t0 = time.perf_counter()
        if policy == "active":
            _, _, target, _ = active_sensing_scores(
                res, coords, noise_std, grid_res, max_particles=800, origin=pos, max_step=max_step
            )
            target = np.array(target, dtype=float)
        elif policy == "chase":
            vec = res.mean[:2] - pos
            d = float(np.hypot(*vec))
            travel = min(float(max_step), max(d - 5.0, 0.0))
            target = pos + (vec / d * travel if d > 1e-6 else 0.0)
        else:  # random
            ang = rng_move.uniform(0.0, 2.0 * np.pi)
            rad = float(max_step) * math.sqrt(rng_move.random())
            target = pos + rad * np.array([math.cos(ang), math.sin(ang)])
        pos = np.clip(target, 2.0, 98.0)
        reading = float(simulate_readings(
            tx, ty, tq, tu, tdir, pos.reshape(1, 2), rng_meas, noise_std=noise_std,
            offsets=[MOBILE_OFFSET])[0])
        mob_xy.append((float(pos[0]), float(pos[1])))
        mob_obs.append(reading)
        res, coords = infer()
        record(s, res, coords, (time.perf_counter() - t0) * 1000.0, reading)
    return history


def run_mobile_benchmark(n_scenarios, n_particles, noise_std, seed, steps, max_step, progress_callback=None):
    """Compare mobile-sensing policies on hidden synthetic leaks (same fixed sensors, same noise draws)."""
    rng = np.random.default_rng(seed)
    policies = ("random", "chase", "active")
    err = {p: np.zeros((int(n_scenarios), int(steps) + 1)) for p in policies}
    fixed_err = np.zeros(int(n_scenarios))
    active_lat, rows = [], []
    for idx in range(int(n_scenarios)):
        tx, ty = float(rng.uniform(15, 85)), float(rng.uniform(15, 85))
        tq, tu, tdir = float(rng.uniform(20, 90)), float(rng.uniform(1.5, 8.0)), float(rng.uniform(0, 360))
        u_obs = float(np.clip(tu + rng.normal(0, 0.5), 0.5, 12.0))
        d_obs = float((tdir + rng.normal(0, 12.0)) % 360.0)
        obs = simulate_readings(tx, ty, tq, tu, tdir, SENSOR_XY, rng, noise_std=noise_std, offsets=SENSOR_OFFSETS)
        start = (float(rng.uniform(10, 90)), float(rng.uniform(10, 90)))
        row = {"Scenario": idx + 1, "True X (m)": round(tx, 2), "True Y (m)": round(ty, 2),
               "Mobile start X": round(start[0], 1), "Mobile start Y": round(start[1], 1)}
        for p in policies:
            hist = run_mobile_mission((tx, ty, tq, tu, tdir), obs, (u_obs, d_obs), (0.7, 18.0), start,
                                      steps, max_step, p, n_particles, noise_std, seed + 2000 + idx, grid_res=13)
            err[p][idx, :] = [h["error"] for h in hist]
            if p == "active":
                active_lat.extend(h["latency_ms"] for h in hist[1:])
        fixed_err[idx] = err["active"][idx, 0]
        row["Fixed-only error (m)"] = round(fixed_err[idx], 2)
        for p in policies:
            row[f"{p.capitalize()} final error (m)"] = round(float(err[p][idx, -1]), 2)
        rows.append(row)
        if progress_callback:
            progress_callback((idx + 1) / n_scenarios, idx + 1)
    lat = np.asarray(active_lat) if active_lat else np.zeros(1)
    fixed_mean = float(np.mean(fixed_err))
    summary = {
        "n": int(n_scenarios), "steps": int(steps), "fixed_mean": fixed_mean,
        "curves": {p: err[p].mean(axis=0) for p in policies},
        "final_mean": {p: float(err[p][:, -1].mean()) for p in policies},
        "final_median": {p: float(np.median(err[p][:, -1])) for p in policies},
        "final_p95": {p: float(np.percentile(err[p][:, -1], 95)) for p in policies},
        "active_vs_fixed_pct": float(100 * (fixed_mean - err["active"][:, -1].mean()) / max(fixed_mean, 1e-9)),
        "active_vs_random_pct": float(100 * (err["random"][:, -1].mean() - err["active"][:, -1].mean())
                                      / max(err["random"][:, -1].mean(), 1e-9)),
        "active_win_rate_vs_random": float(np.mean(err["active"][:, -1] < err["random"][:, -1])),
        "lat_median": float(np.median(lat)), "lat_p95": float(np.percentile(lat, 95)), "lat_max": float(np.max(lat)),
        "within_2s_pct": float(100 * np.mean(lat < HARD_LATENCY_BUDGET_MS)),
    }
    return pd.DataFrame(rows), summary


def run_benchmark(n_scenarios, n_particles, noise_std, seed, progress_callback=None):
    """Run synthetic benchmark and return rows + summary metrics."""
    rng = np.random.default_rng(seed)
    rows = []
    bayes_errors, baseline_errors = [], []
    x_cover, y_cover, joint_cover, frame_times = [], [], [], []
    q_rel_errors = []

    for idx in range(int(n_scenarios)):
        tx = float(rng.uniform(15.0, 85.0))
        ty = float(rng.uniform(15.0, 85.0))
        tq = float(rng.uniform(20.0, 90.0))
        tu = float(rng.uniform(1.5, 8.0))
        tdir = float(rng.uniform(0.0, 360.0))
        # The inference receives noisy wind telemetry, not the true wind values.
        u_obs = float(np.clip(tu + rng.normal(0, 0.5), 0.5, 12.0))
        dir_obs = float((tdir + rng.normal(0, 12.0)) % 360.0)
        obs = simulate_readings(
            tx, ty, tq, tu, tdir, SENSOR_XY, rng, noise_std=noise_std,
            offsets=SENSOR_OFFSETS
        )
        start = time.perf_counter()
        result = particle_filter_frame(
            SENSOR_XY, obs, u_obs, dir_obs, n_particles=n_particles,
            noise_std=noise_std, wind_speed_sd=0.7, wind_dir_sd=18.0,
            seed=seed + 1000 + idx, offsets=SENSOR_OFFSETS
        )
        frame_ms = (time.perf_counter() - start) * 1000.0
        ex, ey, eq = result.mean[:3]
        bayes_err = float(np.hypot(ex - tx, ey - ty))
        base_err, (base_x, base_y) = nearest_sensor_baseline(SENSOR_XY, obs, tx, ty)
        x_ok = result.intervals["x_ci"][0] <= tx <= result.intervals["x_ci"][1]
        y_ok = result.intervals["y_ci"][0] <= ty <= result.intervals["y_ci"][1]
        bayes_errors.append(bayes_err)
        baseline_errors.append(base_err)
        x_cover.append(bool(x_ok))
        y_cover.append(bool(y_ok))
        joint_cover.append(bool(x_ok and y_ok))
        frame_times.append(frame_ms)
        q_rel_errors.append(abs(float(eq) - tq) / max(tq, 1e-9))
        rows.append({
            "Scenario": idx + 1,
            "True X (m)": round(tx, 2), "True Y (m)": round(ty, 2),
            "Estimated X (m)": round(float(ex), 2), "Estimated Y (m)": round(float(ey), 2),
            "Bayesian Error (m)": round(bayes_err, 2),
            "Strongest-Sensor Baseline Error (m)": round(base_err, 2),
            "True Q (relative)": round(tq, 2), "Estimated Q (relative)": round(float(eq), 2),
            "X interval covers truth": bool(x_ok), "Y interval covers truth": bool(y_ok),
            "Joint X/Y coverage": bool(x_ok and y_ok), "Update latency (ms)": round(frame_ms, 3),
        })
        if progress_callback and ((idx + 1) % max(1, n_scenarios // 100) == 0 or idx + 1 == n_scenarios):
            progress_callback((idx + 1) / n_scenarios, idx + 1)

    rows_df = pd.DataFrame(rows)
    summary = {
        "n": int(n_scenarios),
        "bayes_mean": float(np.mean(bayes_errors)),
        "bayes_median": float(np.median(bayes_errors)),
        "bayes_p95": float(np.percentile(bayes_errors, 95)),
        "baseline_mean": float(np.mean(baseline_errors)),
        "baseline_median": float(np.median(baseline_errors)),
        "baseline_p95": float(np.percentile(baseline_errors, 95)),
        "improvement_pct": float(100.0 * (np.mean(baseline_errors) - np.mean(bayes_errors)) /
                                 max(np.mean(baseline_errors), 1e-9)),
        "x_coverage": float(np.mean(x_cover)),
        "y_coverage": float(np.mean(y_cover)),
        "joint_coverage": float(np.mean(joint_cover)),
        "q_rel_error_pct": float(100.0 * np.mean(q_rel_errors)),
        "latency_median": float(np.median(frame_times)),
        "latency_p95": float(np.percentile(frame_times, 95)),
        "latency_max": float(np.max(frame_times)),
        "within_2s_pct": float(100.0 * np.mean(np.asarray(frame_times) < HARD_LATENCY_BUDGET_MS)),
    }
    return rows_df, summary
