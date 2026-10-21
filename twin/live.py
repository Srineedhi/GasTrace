"""Real-time engine: live stream tab, live benchmarks, mission player."""

from __future__ import annotations

import math
import numpy as np
import pandas as pd
import streamlit as st
import time


from . import alerts, config, inference, mission, physics, plots, ui  # noqa: F401


# ============================ REAL-TIME ENGINE (v3) ============================
# Live streaming twin, live benchmarks and mission player. Each public function receives `ctx`,
# a dict of the sidebar values (seed, leak_x, ...); helpers are looked up in the twin modules.

_HELPER_MODULES = (config, physics, inference, mission, alerts, plots, ui)

LIVE_KEY = "ps15_live_state"


class _N:
    """Attribute access: sidebar/context values first, then helpers from the twin modules."""

    def __init__(self, ctx):
        self.__dict__["_ctx"] = ctx

    def __getattr__(self, name):
        ctx = self.__dict__["_ctx"]
        if name in ctx:
            return ctx[name]
        for mod in _HELPER_MODULES:
            if hasattr(mod, name):
                return getattr(mod, name)
        raise AttributeError(name)


def _fragment(run_every):
    frag = getattr(st, "fragment", None) or getattr(st, "experimental_fragment", None)

    def deco(fn):
        if frag is None:
            return fn
        try:
            return frag(run_every=run_every)(fn)
        except TypeError:  # very old Streamlit without run_every
            return frag(fn)

    return deco


# =============================================================================
# 1. LIVE STREAM
# =============================================================================
def _fresh_state(n):
    return {
        "tick": 0,
        "rng": np.random.default_rng(int(n.seed) + 31337),
        "x": float(n.leak_x), "y": float(n.leak_y), "vx": 1.4, "vy": 0.9,
        "dir": float(n.wind_from), "u": float(n.wind_speed),
        "dock": (float(n.mob_start_x), float(n.mob_start_y)),
        "pos": np.array([float(n.mob_start_x), float(n.mob_start_y)]),
        "trail": [],           # (x, y, reading) of mobile samples still in memory
        "hist": [],            # per-tick metrics
        "view": None,          # cached rendering (shown while paused)
        "cover_x": 0, "cover_y": 0, "frames": 0,
    }


def _advance_world(S, veer, move, dt):
    r = S["rng"]
    S["tick"] += 1
    if veer:
        S["dir"] = (S["dir"] + (math.sin(S["tick"] * 0.15) * 6.0 + r.normal(0, 5.0)) * dt) % 360.0
        S["u"] = float(np.clip(S["u"] + r.normal(0, 0.35) * dt, 0.5, 10.0))
    if move:
        S["x"] += S["vx"] * dt
        S["y"] += S["vy"] * dt
        if S["x"] < 8 or S["x"] > 92:
            S["vx"] *= -1
            S["x"] = float(np.clip(S["x"], 8, 92))
        if S["y"] < 8 or S["y"] > 92:
            S["vy"] *= -1
            S["y"] = float(np.clip(S["y"], 8, 92))


def _tick(ctx, S, advance, veer, move, dt, n_particles, mob_on, mem):
    """One real-time cycle: (move world) -> new noisy readings -> infer -> choose/take mobile sample."""
    n = _N(ctx)
    if advance:
        _advance_world(S, veer, move, dt)
    rng = S["rng"]
    noise = float(n.measurement_noise)
    q = float(n.strength)

    # --- new fixed-sensor readings + noisy wind telemetry (the estimator never sees the truth) ---
    fixed = n.simulate_readings(S["x"], S["y"], q, S["u"], S["dir"], n.SENSOR_XY, rng,
                                noise_std=noise, offsets=n.SENSOR_OFFSETS)
    u_obs = float(np.clip(S["u"] + rng.normal(0, n.wind_speed_sd), 0.5, 12.0))
    d_obs = float((S["dir"] + rng.normal(0, n.wind_dir_sd)) % 360.0)

    # --- mobile sensor memory: static scene keeps samples, dynamic scene forgets quickly ---
    dynamic = bool(veer or move)
    keep = max(1, min(int(mem), 2 if dynamic else int(mem)))
    if not mob_on:
        S["trail"] = []
    S["trail"] = S["trail"][-keep:] if S["trail"] else []

    coords = n.SENSOR_XY
    obs = fixed
    offs = n.SENSOR_OFFSETS
    if S["trail"]:
        tx = np.array([[t[0], t[1]] for t in S["trail"]])
        coords = np.vstack([n.SENSOR_XY, tx])
        obs = np.concatenate([fixed, [t[2] for t in S["trail"]]])
        offs = np.concatenate([n.SENSOR_OFFSETS, np.full(len(S["trail"]), n.MOBILE_OFFSET)])

    t0 = time.perf_counter()
    res = n.particle_filter_frame(
        coords, obs, u_obs, d_obs, n_particles=n_particles, noise_std=noise,
        wind_speed_sd=n.wind_speed_sd, wind_dir_sd=n.wind_dir_sd,
        seed=int(n.seed) + 1 + S["tick"], offsets=offs,
    )
    target = None
    if mob_on:
        _, _, target, _ = n.active_sensing_scores(
            res, coords, noise, 13, max_particles=800, origin=S["pos"], max_step=float(n.mob_max_step))
    latency = (time.perf_counter() - t0) * 1000.0

    # --- evaluation-only metrics vs the hidden truth ---
    ex, ey = float(res.mean[0]), float(res.mean[1])
    err = float(math.hypot(ex - S["x"], ey - S["y"]))
    base_err, base_xy = n.nearest_sensor_baseline(n.SENSOR_XY, fixed, S["x"], S["y"])
    ci_w = 0.5 * ((res.intervals["x_ci"][1] - res.intervals["x_ci"][0]) +
                  (res.intervals["y_ci"][1] - res.intervals["y_ci"][0]))
    x_ok = res.intervals["x_ci"][0] <= S["x"] <= res.intervals["x_ci"][1]
    y_ok = res.intervals["y_ci"][0] <= S["y"] <= res.intervals["y_ci"][1]
    S["frames"] += 1
    S["cover_x"] += int(x_ok)
    S["cover_y"] += int(y_ok)
    S["hist"].append({"tick": S["tick"], "Twin error (m)": err, "Baseline error (m)": base_err,
                      "Latency (ms)": latency, "95% CI width (m)": ci_w, "ESS": float(res.ess)})
    del S["hist"][:-150]

    # --- render (cached so that a paused stream does not re-draw every second) ---
    peak = float(np.max(fixed))
    thr = float(n.alarm_threshold)
    if peak >= thr:
        leak_pill = n.pill("CRITICAL LEAK DETECTED", "red")
    elif peak >= 0.5 * thr:
        leak_pill = n.pill("ELEVATED CONCENTRATION · MONITORING", "amber")
    else:
        leak_pill = n.pill("NO ALARM · ALL NODES BELOW THRESHOLD", "green")
    if latency < n.EDGE_LATENCY_TARGET_MS:
        lat_pill = n.pill(f"EDGE LATENCY OK · {latency:.0f} ms", "green")
    elif latency < n.HARD_LATENCY_BUDGET_MS:
        lat_pill = n.pill(f"LATENCY {latency:.0f} ms · ABOVE 50 ms TARGET, WITHIN 2 s", "amber")
    else:
        lat_pill = n.pill(f"LATENCY BUDGET EXCEEDED · {latency:.0f} ms", "red")
    post_pill = n.pill(f"95% CI WIDTH {ci_w:.0f} m · ESS {res.ess:.0f}",
                       "green" if (ci_w < 25 and res.ess >= 15) else "amber")
    n_meas = len(obs)
    tick_pill = n.pill(f"LIVE · TICK {S['tick']} · {n_meas} MEASUREMENTS", "blue")

    hist = S["hist"]
    recent = hist[-30:]
    mean_t = float(np.mean([h["Twin error (m)"] for h in recent]))
    mean_b = float(np.mean([h["Baseline error (m)"] for h in recent]))
    mean_l = float(np.mean([h["Latency (ms)"] for h in recent]))
    max_l = float(np.max([h["Latency (ms)"] for h in recent]))
    cx = 100.0 * S["cover_x"] / S["frames"]
    cy = 100.0 * S["cover_y"] / S["frames"]
    kpis = [
        n.kpi("Twin error now*", f"{err:.1f} m", f"baseline {base_err:.1f} m", "green" if err < base_err else "amber"),
        n.kpi("Rolling mean (30)*", f"{mean_t:.1f} m", f"baseline {mean_b:.1f} m", "green" if mean_t < mean_b else "red"),
        n.kpi("Rolling latency", f"{mean_l:.0f} ms", f"max {max_l:.0f} ms", "green" if max_l < n.HARD_LATENCY_BUDGET_MS else "red"),
        n.kpi("Live X/Y coverage*", f"{cx:.0f}% / {cy:.0f}%", f"over {S['frames']} frames"),
        n.kpi("True wind (sim)", f"{S['dir']:.0f}° · {S['u']:.1f} m/s", "drifting" if veer else "fixed"),
        n.kpi("True leak (sim)", f"({S['x']:.0f}, {S['y']:.0f}) m", "moving" if move else "fixed"),
    ]
    mobile = None
    if mob_on:
        mobile = {"start": S["dock"], "trail": list(S["trail"]), "route_to": target}
    fig = n.draw_tactical_map(res, fixed, len(fixed), n.layers, thr, truth=(S["x"], S["y"]),
                              active_point=target, baseline_xy=base_xy, figsize=(10.5, 6.6), mobile=mobile)
    map_html = n.hud(n.fig_img(fig, dpi=110), "LIVE TOPOGRAPHIC PROBABILITY MAP",
                     f"TICK {S['tick']} · {n_particles:,} PARTICLES · RE-INFERRED EVERY TICK")
    S["view"] = {"pills": f"<div class='pill-row'>{leak_pill}{lat_pill}{post_pill}{tick_pill}</div>",
                 "kpis": kpis, "map": map_html}

    # --- mobile sensor takes its next sample (becomes part of the NEXT inference) ---
    if mob_on and advance and target is not None:
        S["pos"] = np.clip(np.array(target, dtype=float), 2.0, 98.0)
        r = float(n.simulate_readings(S["x"], S["y"], q, S["u"], S["dir"], S["pos"].reshape(1, 2), rng,
                                      noise_std=noise, offsets=[n.MOBILE_OFFSET])[0])
        S["trail"].append((float(S["pos"][0]), float(S["pos"][1]), r))


def _show(ctx, S):
    n = _N(ctx)
    v = S["view"]
    if v is None:
        return
    n.md(v["pills"])
    n.kpi_row(v["kpis"])
    n.md(v["map"])
    df = pd.DataFrame(S["hist"]).set_index("tick")
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Localisation error over time (lower is better)")
        st.line_chart(df[["Twin error (m)", "Baseline error (m)"]], height=220)
    with c2:
        st.caption("Update latency (ms) and posterior width (m)")
        st.line_chart(df[["Latency (ms)", "95% CI width (m)"]], height=220)
    st.caption("*Evaluation-only: possible because the simulator knows the hidden truth. "
               "Mobile samples older than the memory window are dropped when the scene is dynamic.")


def render_live_stream(ctx):
    """Call inside a tab:  render_live_stream(globals())"""
    n = _N(ctx)
    ss = st.session_state
    if LIVE_KEY not in ss:
        ss[LIVE_KEY] = _fresh_state(n)

    c1, c2, c3, c4 = st.columns([1.1, 1, 1, 1])
    with c1:
        st.toggle("▶ Stream live readings", value=False, key="live_run",
                  help="Each second: new noisy readings, new inference, new mobile sample.")
    with c2:
        st.toggle("Wind veer + turbulence", value=True, key="live_veer")
        st.toggle("Moving leak", value=False, key="live_move")
    with c3:
        st.select_slider("Particles per tick", options=[500, 1000, 1500, 2000, 3000], value=1000, key="live_particles")
        st.slider("Simulation speed", 0.5, 4.0, 1.0, 0.5, key="live_speed")
    with c4:
        st.toggle("Mobile sensor active", value=bool(n.mobile_enabled), key="live_mob")
        if st.button("Reset stream", key="live_reset"):
            ss[LIVE_KEY] = _fresh_state(n)

    S = ss[LIVE_KEY]

    @_fragment(run_every=1.0)
    def live_body():
        running = bool(st.session_state.get("live_run", False))
        if running or S["view"] is None:
            _tick(ctx, S, advance=running,
                  veer=bool(st.session_state.get("live_veer", True)),
                  move=bool(st.session_state.get("live_move", False)),
                  dt=float(st.session_state.get("live_speed", 1.0)),
                  n_particles=int(st.session_state.get("live_particles", 1000)),
                  mob_on=bool(st.session_state.get("live_mob", False)),
                  mem=int(n.mob_steps))
        _show(ctx, S)

    live_body()
    if not hasattr(st, "fragment") and not hasattr(st, "experimental_fragment"):
        st.warning("This Streamlit version has no fragments; upgrade (`pip install -U streamlit`) for auto-refresh. "
                   "Use the button to step manually.")
        if st.button("Step once", key="live_step"):
            _tick(ctx, S, True, True, False, 1.0, 1000, bool(n.mobile_enabled), int(n.mob_steps))


# =============================================================================
# 2. LIVE BENCHMARKS
# =============================================================================
def _bench_metrics(n, b, base, xc, yc, jc, ft, qr):
    ft = np.asarray(ft)
    return {
        "n": len(b),
        "bayes_mean": float(np.mean(b)), "bayes_median": float(np.median(b)), "bayes_p95": float(np.percentile(b, 95)),
        "baseline_mean": float(np.mean(base)), "baseline_median": float(np.median(base)),
        "baseline_p95": float(np.percentile(base, 95)),
        "improvement_pct": float(100.0 * (np.mean(base) - np.mean(b)) / max(np.mean(base), 1e-9)),
        "x_coverage": float(np.mean(xc)), "y_coverage": float(np.mean(yc)), "joint_coverage": float(np.mean(jc)),
        "q_rel_error_pct": float(100.0 * np.mean(qr)),
        "latency_median": float(np.median(ft)), "latency_p95": float(np.percentile(ft, 95)),
        "latency_max": float(np.max(ft)),
        "within_2s_pct": float(100.0 * np.mean(ft < n.HARD_LATENCY_BUDGET_MS)),
    }


def run_benchmark_live(ctx, n_scenarios, n_particles, noise_std, seed, refresh_every=None):
    """Same maths as run_benchmark, but KPIs + CDF update while it runs. Partial results survive an interrupt."""
    n = _N(ctx)
    n_scenarios = int(n_scenarios)
    refresh_every = refresh_every or max(1, n_scenarios // 40)
    rng = np.random.default_rng(seed)
    rows, b, base, xc, yc, jc, ft, qr = [], [], [], [], [], [], [], []
    bar = st.progress(0.0)
    kslot, cslot = st.empty(), st.empty()
    st.caption("Live run: results update as scenarios complete. Changing any widget interrupts the run; "
               "everything finished so far is kept.")
    for idx in range(n_scenarios):
        tx, ty = float(rng.uniform(15, 85)), float(rng.uniform(15, 85))
        tq, tu, tdir = float(rng.uniform(20, 90)), float(rng.uniform(1.5, 8.0)), float(rng.uniform(0, 360))
        u_obs = float(np.clip(tu + rng.normal(0, 0.5), 0.5, 12.0))
        d_obs = float((tdir + rng.normal(0, 12.0)) % 360.0)
        obs = n.simulate_readings(tx, ty, tq, tu, tdir, n.SENSOR_XY, rng, noise_std=noise_std, offsets=n.SENSOR_OFFSETS)
        t0 = time.perf_counter()
        res = n.particle_filter_frame(n.SENSOR_XY, obs, u_obs, d_obs, n_particles=n_particles, noise_std=noise_std,
                                      wind_speed_sd=0.7, wind_dir_sd=18.0, seed=seed + 1000 + idx,
                                      offsets=n.SENSOR_OFFSETS)
        ms = (time.perf_counter() - t0) * 1000.0
        ex, ey, eq = res.mean[:3]
        e = float(math.hypot(ex - tx, ey - ty))
        be, _ = n.nearest_sensor_baseline(n.SENSOR_XY, obs, tx, ty)
        xo = res.intervals["x_ci"][0] <= tx <= res.intervals["x_ci"][1]
        yo = res.intervals["y_ci"][0] <= ty <= res.intervals["y_ci"][1]
        b.append(e); base.append(be); xc.append(xo); yc.append(yo); jc.append(xo and yo); ft.append(ms)
        qr.append(abs(float(eq) - tq) / max(tq, 1e-9))
        rows.append({
            "Scenario": idx + 1, "True X (m)": round(tx, 2), "True Y (m)": round(ty, 2),
            "Estimated X (m)": round(float(ex), 2), "Estimated Y (m)": round(float(ey), 2),
            "Bayesian Error (m)": round(e, 2), "Strongest-Sensor Baseline Error (m)": round(be, 2),
            "True Q (relative)": round(tq, 2), "Estimated Q (relative)": round(float(eq), 2),
            "X interval covers truth": bool(xo), "Y interval covers truth": bool(yo),
            "Joint X/Y coverage": bool(xo and yo), "Update latency (ms)": round(ms, 3),
        })
        done = idx + 1
        if done % refresh_every == 0 or done == n_scenarios:
            m = _bench_metrics(n, b, base, xc, yc, jc, ft, qr)
            df = pd.DataFrame(rows)
            st.session_state["ps15_benchmark_df"] = df          # keep partial results
            st.session_state["ps15_benchmark_metrics"] = m
            bar.progress(done / n_scenarios, text=f"Scenario {done} / {n_scenarios}")
            kslot.markdown(
                f"**Running:** twin mean **{m['bayes_mean']:.2f} m** vs baseline **{m['baseline_mean']:.2f} m** "
                f"({m['improvement_pct']:+.1f}%) · joint coverage **{100 * m['joint_coverage']:.0f}%** · "
                f"P95 latency **{m['latency_p95']:.1f} ms**")
            cslot.pyplot(n.draw_bench_cdf(df), clear_figure=True) if len(df) > 2 else None
    bar.empty(); kslot.empty(); cslot.empty()
    return pd.DataFrame(rows), _bench_metrics(n, b, base, xc, yc, jc, ft, qr)


def run_mobile_benchmark_live(ctx, n_scenarios, n_particles, noise_std, seed, steps, max_step):
    """Mobile-policy benchmark that refreshes its comparison chart after every finished scenario."""
    n = _N(ctx)
    n_scenarios, steps = int(n_scenarios), int(steps)
    rng = np.random.default_rng(seed)
    policies = ("random", "chase", "active")
    err = {p: np.zeros((n_scenarios, steps + 1)) for p in policies}
    fixed_err = np.zeros(n_scenarios)
    lat, rows = [], []
    bar = st.progress(0.0)
    kslot, cslot = st.empty(), st.empty()
    st.caption("Live run: each finished scenario updates the chart. Changing a widget interrupts; partial results are kept.")

    def summary(k):
        fe = float(np.mean(fixed_err[:k]))
        L = np.asarray(lat) if lat else np.zeros(1)
        rm = {p: float(err[p][:k, -1].mean()) for p in policies}
        return {
            "n": k, "steps": steps, "fixed_mean": fe,
            "curves": {p: err[p][:k].mean(axis=0) for p in policies},
            "final_mean": rm,
            "final_median": {p: float(np.median(err[p][:k, -1])) for p in policies},
            "final_p95": {p: float(np.percentile(err[p][:k, -1], 95)) for p in policies},
            "active_vs_fixed_pct": float(100 * (fe - rm["active"]) / max(fe, 1e-9)),
            "active_vs_random_pct": float(100 * (rm["random"] - rm["active"]) / max(rm["random"], 1e-9)),
            "active_win_rate_vs_random": float(np.mean(err["active"][:k, -1] < err["random"][:k, -1])),
            "lat_median": float(np.median(L)), "lat_p95": float(np.percentile(L, 95)), "lat_max": float(np.max(L)),
            "within_2s_pct": float(100 * np.mean(L < n.HARD_LATENCY_BUDGET_MS)),
        }

    for idx in range(n_scenarios):
        tx, ty = float(rng.uniform(15, 85)), float(rng.uniform(15, 85))
        tq, tu, tdir = float(rng.uniform(20, 90)), float(rng.uniform(1.5, 8.0)), float(rng.uniform(0, 360))
        u_obs = float(np.clip(tu + rng.normal(0, 0.5), 0.5, 12.0))
        d_obs = float((tdir + rng.normal(0, 12.0)) % 360.0)
        obs = n.simulate_readings(tx, ty, tq, tu, tdir, n.SENSOR_XY, rng, noise_std=noise_std, offsets=n.SENSOR_OFFSETS)
        start = (float(rng.uniform(10, 90)), float(rng.uniform(10, 90)))
        row = {"Scenario": idx + 1, "True X (m)": round(tx, 2), "True Y (m)": round(ty, 2),
               "Mobile start X": round(start[0], 1), "Mobile start Y": round(start[1], 1)}
        for p in policies:
            hist = n.run_mobile_mission((tx, ty, tq, tu, tdir), obs, (u_obs, d_obs), (0.7, 18.0), start, steps,
                                        max_step, p, n_particles, noise_std, seed + 2000 + idx, grid_res=13)
            err[p][idx, :] = [h["error"] for h in hist]
            if p == "active":
                lat.extend(h["latency_ms"] for h in hist[1:])
        fixed_err[idx] = err["active"][idx, 0]
        row["Fixed-only error (m)"] = round(float(fixed_err[idx]), 2)
        for p in policies:
            row[f"{p.capitalize()} final error (m)"] = round(float(err[p][idx, -1]), 2)
        rows.append(row)
        done = idx + 1
        s = summary(done)
        st.session_state["ps15_mobile_df"] = pd.DataFrame(rows)    # keep partial results
        st.session_state["ps15_mobile_sum"] = s
        bar.progress(done / n_scenarios, text=f"Mobile scenario {done} / {n_scenarios}")
        kslot.markdown(
            f"**Running:** fixed-only **{s['fixed_mean']:.2f} m** · active **{s['final_mean']['active']:.2f} m** · "
            f"chase **{s['final_mean']['chase']:.2f} m** · random **{s['final_mean']['random']:.2f} m** · "
            f"active vs fixed **{s['active_vs_fixed_pct']:+.1f}%**")
        if done >= 2 and (done % 2 == 0 or done == n_scenarios):
            cslot.pyplot(n.draw_mobile_bench(s), clear_figure=True)
    bar.empty(); kslot.empty(); cslot.empty()
    return pd.DataFrame(rows), summary(n_scenarios)


# =============================================================================
# 3. MOBILE MISSION PLAYER
# =============================================================================
def render_mission_player(ctx, mission, delay_default=0.8):
    """Plays a precomputed closed-loop mission frame by frame. Call after run_mobile_mission(...)."""
    n = _N(ctx)
    pc1, pc2 = st.columns([1, 2])
    with pc1:
        play = st.button("▶ Play mission live", key="mission_play", type="primary")
    with pc2:
        delay = st.slider("Seconds per mobile sample", 0.2, 3.0, float(delay_default), 0.1, key="mission_delay")
    if not play:
        return
    slot = st.empty()
    thr = float(n.alarm_threshold)
    for f, h in enumerate(mission):
        trail = [(m["pos"][0], m["pos"][1], m["reading"]) for m in mission[1:f + 1]]
        _, _, nxt, _ = n.active_sensing_scores(h["result"], h["coords"], n.measurement_noise, 13,
                                                 origin=h["pos"], max_step=float(n.mob_max_step))
        fig = n.draw_tactical_map(
            h["result"], ctx["readings"], n.N_SENSORS, n.layers, thr, truth=(n.leak_x, n.leak_y),
            active_point=nxt if f < len(mission) - 1 else None,
            mobile={"start": (n.mob_start_x, n.mob_start_y), "trail": trail, "route_to": None}, figsize=(10.0, 6.3))
        info = (f"SAMPLE {f}/{len(mission) - 1} · ERROR {h['error']:.1f} m · CI WIDTH {h['ci_w']:.0f} m · "
                f"UPDATE {h['latency_ms']:.0f} ms")
        slot.markdown(n.H(n.hud(n.fig_img(fig, dpi=110), "MOBILE MISSION · LIVE PLAYBACK", info)),
                      unsafe_allow_html=True)
        if f < len(mission) - 1:
            time.sleep(float(delay))
