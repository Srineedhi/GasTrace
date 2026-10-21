"""Streamlit entry point: sidebar, computation and tabs."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import time

from twin.alerts import alerts_html, build_alerts, update_event_log
from twin.config import EDGE_LATENCY_TARGET_MS, HARD_LATENCY_BUDGET_MS, N_SENSORS, POLICY_LABELS, SENSOR_NAMES, SENSOR_OFFSETS, SENSOR_XY
from twin.inference import active_sensing_scores, nearest_sensor_baseline, particle_filter_frame
from twin.interactive import build_interactive_html
from twin.live import render_live_stream, render_mission_player, run_benchmark_live, run_mobile_benchmark_live
from twin.mission import run_mobile_mission
from twin.panels import ci_panel, scada_panel, wind_panel
from twin.physics import simulate_readings
from twin.plots import draw_bench_cdf, draw_bench_coverage, draw_bench_summary, draw_dispersion, draw_info_map, draw_mission_chart, draw_mobile_bench, draw_tactical_map
from twin.styles import CSS
from twin.ui import H, callout, cardinal, fig_img, hud, kpi, kpi_row, level_of, md, pill, show_df, wind_label


# ------------------------------- Page setup ----------------------------------
st.set_page_config(
    page_title="TECHNOVA 2026 | Gas Leak Digital Twin",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------- App shell -----------------------------------
st.markdown(H(CSS), unsafe_allow_html=True)

md(
    f"""
    <div class='hero'>
      <div>
        <div class='eyebrow'>TECHNOVA 2026 · PROBLEM STATEMENT PS-15</div>
        <div class='title'>Gas Leak Digital Twin</div>
        <div class='subtitle'>Physics-informed source localisation · Bayesian uncertainty · Mobile active sensing</div>
      </div>
      <div>
        <span class='badge'>SIMULATION MODE</span>
        <span class='badge'>SMC / PARTICLE FILTER</span>
        <span class='badge'>MOBILE SENSOR</span>
        <span class='badge'>FRAME {time.strftime('%H:%M:%S')}</span>
      </div>
    </div>
    """
)
banner_slot = st.container()
st.caption(
    "Simulation-first prototype. Ground truth is shown only for evaluation; "
    "the estimator receives sensor observations and noisy wind telemetry."
)

# -------------------------------- Sidebar ------------------------------------
alerts_box = st.sidebar.container()  # filled after computation (live alerts + event log)
st.sidebar.markdown(
    "<div style='font-weight:800;letter-spacing:.14em;font-size:.8rem;color:#7dd3fc;margin:.4rem 0 .3rem'>MISSION CONTROL</div>",
    unsafe_allow_html=True,
)

with st.sidebar.expander("◎ Source control", expanded=False):
    leak_x = st.slider("Simulated leak X (m)", 0, 100, 55)
    leak_y = st.slider("Simulated leak Y (m)", 0, 100, 55)
    strength = st.slider("Release rate Q (relative units)", 10, 100, 90)

with st.sidebar.expander("🌬 Wind & environment", expanded=False):
    wind_speed = st.slider("True wind speed (m/s)", 1.0, 10.0, 3.5, 0.5)
    wind_from = st.slider("True wind direction FROM north (°)", 0, 359, 225)
    wind_speed_sd = st.slider("Wind-speed telemetry uncertainty (m/s)", 0.1, 3.0, 0.7, 0.1)
    wind_dir_sd = st.slider("Wind-direction telemetry uncertainty (°)", 1.0, 90.0, 18.0, 1.0)

with st.sidebar.expander("⚙ Settings", expanded=False):
    measurement_noise = st.slider("Sensor noise (model units)", 0.05, 2.0, 0.2, 0.05)
    alarm_threshold = st.slider("Alarm threshold (model units)", 0.2, 5.0, 1.0, 0.1)
    n_particles = st.select_slider("Inference particles", options=[1000, 2000, 4000, 6000, 8000], value=4000)
    seed = int(st.number_input("Random seed", min_value=0, max_value=999999, value=42, step=1))
    k_assim = st.slider("Fixed-sensor readings assimilated", 1, N_SENSORS, N_SENSORS,
                        help="Feed the estimator one sensor at a time to watch the posterior collapse.")
    expanded_view = st.toggle("Expanded view for Interactive Twin", value=False,
                              help="Makes the interactive twin taller/larger (fallback if browser full screen is blocked).")

with st.sidebar.expander("🛰 Mobile sensor", expanded=False):
    mobile_enabled = st.toggle("Deploy mobile sensor", value=True)
    mob_start_x = st.slider("Mobile start X (m)", 0, 100, 50)
    mob_start_y = st.slider("Mobile start Y (m)", 0, 100, 8)
    mob_steps = st.slider("Mobile samples in mission", 1, 8, 5)
    mob_max_step = st.slider("Max move per sample (m)", 10, 60, 30, 5)
    mob_policy = st.radio("Mobile policy", list(POLICY_LABELS), format_func=lambda p: POLICY_LABELS[p], index=0)

LAYER_OPTIONS = {
    "Posterior probability": "posterior",
    "95% credible box": "box",
    "Predicted alarm contours": "plume",
    "Wind vectors": "wind",
    "Range rings": "rings",
    "Particle cloud": "cloud",
    "Strongest-sensor baseline": "baseline",
}
with st.sidebar.expander("🗺 Map layers", expanded=False):
    layer_labels = st.multiselect(
        "Layers", list(LAYER_OPTIONS),
        default=["Posterior probability", "95% credible box", "Predicted alarm contours", "Wind vectors", "Range rings"],
    )
layers = {LAYER_OPTIONS[x] for x in layer_labels}

# Separate ground truth from estimator inputs by creating noisy wind telemetry.
rng = np.random.default_rng(seed)
observed_wind_speed = float(np.clip(wind_speed + rng.normal(0, wind_speed_sd), 0.5, 12.0))
observed_wind_from = float((wind_from + rng.normal(0, wind_dir_sd)) % 360.0)
readings = simulate_readings(
    leak_x, leak_y, strength, wind_speed, wind_from, SENSOR_XY, rng,
    noise_std=measurement_noise, offsets=SENSOR_OFFSETS
)

# ------------------------------ Core computation -----------------------------
infer_start = time.perf_counter()
result = particle_filter_frame(
    SENSOR_XY[:k_assim], readings[:k_assim], observed_wind_speed, observed_wind_from,
    n_particles=n_particles, noise_std=measurement_noise,
    wind_speed_sd=wind_speed_sd, wind_dir_sd=wind_dir_sd,
    seed=seed + 1, offsets=SENSOR_OFFSETS[:k_assim]
)
latency_ms = (time.perf_counter() - infer_start) * 1000.0
ex, ey, eq, eu, etheta = result.mean
error_m = float(np.hypot(ex - leak_x, ey - leak_y))
base_err, base_xy = nearest_sensor_baseline(SENSOR_XY, readings, leak_x, leak_y)
active_grid, active_scores, active_point, active_score = active_sensing_scores(
    result, SENSOR_XY, noise_std=measurement_noise,
    origin=(mob_start_x, mob_start_y) if mobile_enabled else None,
    max_step=mob_max_step if mobile_enabled else None,
)
peak_reading = float(np.max(readings))

# Alerts, banner and event log (all computed from live values).
headline, alert_items = build_alerts(
    readings, k_assim, alarm_threshold, result, latency_ms,
    mobile_point=active_point if mobile_enabled else None,
)
params = dict(leak_x=leak_x, leak_y=leak_y, strength=strength, wind_speed=wind_speed, wind_from=wind_from,
              alarm_threshold=alarm_threshold, measurement_noise=measurement_noise, k_assim=k_assim,
              mob_start_x=mob_start_x, mob_start_y=mob_start_y, mob_steps=mob_steps, mob_policy=mob_policy,
              n_particles=n_particles)
levels_now = {SENSOR_NAMES[i]: level_of(float(readings[i]), alarm_threshold)[1] for i in range(N_SENSORS)}
event_log = update_event_log(params, levels_now, peak_reading >= alarm_threshold, (float(ex), float(ey)))
n_active = sum(1 for kind, title, _ in alert_items if kind in ("red", "amber"))

with banner_slot:
    nb1, nb2 = st.columns([6, 1])
    with nb1:
        md(f"<div class='notice {headline[0]}'><div class='n-ico'>{headline[1].split(' ')[0]}</div>"
           f"<div><div class='n-title'>{' '.join(headline[1].split(' ')[1:])}</div>"
           f"<div class='n-sub mono'>{headline[2]}</div></div></div>")
    with nb2:
        if hasattr(st, "popover"):
            with st.popover(f"🔔 Alerts ({n_active})", use_container_width=True):
                md(alerts_html(alert_items))
        else:
            st.button(f"🔔 Alerts ({n_active})", disabled=True)

with alerts_box:
    st.markdown("<div class='side-title'>🔔 LIVE ALERTS</div>", unsafe_allow_html=True)
    md(f"<div class='alert {headline[0]}'><b>{headline[1]}</b><br>{headline[2]}</div>")
    md(alerts_html([it for it in alert_items if it[1].split(' ')[0] in SENSOR_NAMES]))
    with st.expander("Event log (what changed)", expanded=False):
        if event_log:
            md("".join(f"<div class='evline'>{t} · {m}</div>" for t, _, m in reversed(event_log)))
        else:
            st.caption("Change any control to see events here.")

# Values the real-time engine (twin/live.py) needs from the sidebar / current frame.
ctx = dict(
    seed=seed,
    leak_x=leak_x,
    leak_y=leak_y,
    strength=strength,
    wind_speed=wind_speed,
    wind_from=wind_from,
    wind_speed_sd=wind_speed_sd,
    wind_dir_sd=wind_dir_sd,
    measurement_noise=measurement_noise,
    alarm_threshold=alarm_threshold,
    mobile_enabled=mobile_enabled,
    mob_start_x=mob_start_x,
    mob_start_y=mob_start_y,
    mob_steps=mob_steps,
    mob_max_step=mob_max_step,
    layers=layers,
    readings=readings,
)

# -------------------------------- Tabs ---------------------------------------
tab_inter, tab_live, tab_stream, tab_mobile, tab_bench, tab_lab = st.tabs([
    "Interactive Twin", "Live Digital Twin", "Live Stream", "Mobile Sensing", "Benchmark & Validation", "What-if Lab"
])

with tab_inter:
    st.markdown("### Interactive digital twin: drag the leak, the sensors, the mobile sensor and the wind")
    st.caption(
        "Use the left tool rail inside the twin (⚙ Settings, ◎ Source, 🛰 Mobile, 🔔 Alerts). Press ▶ Simulate for live wind veer / "
        "moving leak, and ⛶ Full screen for a bigger map. The twin re-infers on every change. Starting values come from the "
        "sidebar; moves made here are not sent back to the other tabs."
    )
    interactive_cfg = {
        "leak_x": float(leak_x), "leak_y": float(leak_y), "strength": float(strength),
        "wind_speed": float(wind_speed), "wind_from": float(wind_from),
        "wind_speed_sd": float(wind_speed_sd), "wind_dir_sd": float(wind_dir_sd),
        "noise": float(measurement_noise), "threshold": float(alarm_threshold),
        "n_particles": int(min(n_particles, 8000)), "seed": int(seed),
        "mobile_on": bool(mobile_enabled), "mobile_x": float(mob_start_x), "mobile_y": float(mob_start_y),
        "mobile_len": int(mob_steps), "expanded": bool(expanded_view), "open_panel": "alerts",
        "sensors": [
            {"name": n, "x": float(SENSOR_XY[i, 0]), "y": float(SENSOR_XY[i, 1]), "off": float(SENSOR_OFFSETS[i])}
            for i, n in enumerate(SENSOR_NAMES)
        ],
    }
    interactive_html = build_interactive_html(interactive_cfg)
    iframe_height = 1500 if expanded_view else 1080
    if hasattr(st, "iframe"):  # newer Streamlit; components.v1.html is deprecated there
        st.iframe(interactive_html, height=iframe_height)
    else:
        components.html(interactive_html, height=iframe_height, scrolling=True)

with tab_stream:
    st.markdown("### Live stream: new readings, new inference, every second")
    st.caption("Flip the toggle to stream. Each tick draws fresh noisy sensor readings and wind telemetry, moves the "
               "hidden world (wind veer, optional moving leak), re-runs the particle filter and lets the mobile sensor "
               "take its next informative sample. Starting values come from the sidebar.")
    render_live_stream(ctx)

with tab_live:
    if peak_reading >= alarm_threshold:
        leak_pill = pill("CRITICAL LEAK DETECTED", "red")
    elif peak_reading >= 0.5 * alarm_threshold:
        leak_pill = pill("ELEVATED CONCENTRATION · MONITORING", "amber")
    else:
        leak_pill = pill("NO ALARM · ALL NODES BELOW THRESHOLD", "green")

    if latency_ms < EDGE_LATENCY_TARGET_MS:
        lat_pill = pill(f"CYBER-PHYSICAL EDGE LATENCY CALIBRATED · {latency_ms:.0f} ms", "green")
    elif latency_ms < HARD_LATENCY_BUDGET_MS:
        lat_pill = pill(f"LATENCY {latency_ms:.0f} ms · ABOVE 50 ms EDGE TARGET, WITHIN 2 s BUDGET", "amber")
    else:
        lat_pill = pill(f"LATENCY BUDGET EXCEEDED · {latency_ms:.0f} ms", "red")

    ci_w = 0.5 * ((result.intervals["x_ci"][1] - result.intervals["x_ci"][0]) +
                  (result.intervals["y_ci"][1] - result.intervals["y_ci"][0]))
    if result.ess < 15:
        post_pill = pill(f"LOW PARTICLE DIVERSITY · ESS {result.ess:.0f} · RAISE PARTICLES", "amber")
    elif ci_w < 25:
        post_pill = pill(f"POSTERIOR CONVERGED · 95% CI WIDTH {ci_w:.0f} m", "green")
    elif ci_w < 50:
        post_pill = pill(f"POSTERIOR NARROWING · 95% CI WIDTH {ci_w:.0f} m", "amber")
    else:
        post_pill = pill(f"POSTERIOR DIFFUSE · 95% CI WIDTH {ci_w:.0f} m · NEED MORE READINGS", "amber")
    link_pill = pill(f"SENSOR LINK {N_SENSORS}/{N_SENSORS} ONLINE · {k_assim} ASSIMILATED", "blue")
    mob_pill = pill("MOBILE SENSOR READY · SEE MOBILE SENSING TAB", "blue") if mobile_enabled else ""
    md(f"<div class='pill-row'>{leak_pill}{lat_pill}{post_pill}{link_pill}{mob_pill}</div>")

    kpi_row([
        kpi("Sensor nodes", f"{N_SENSORS}", f"{k_assim} feeding estimator", "blue"),
        kpi("Inference particles", f"{n_particles:,}", "SMC importance weights"),
        kpi("Observed wind", f"{observed_wind_speed:.1f} m/s", wind_label(observed_wind_speed)),
        kpi("Wind direction", f"{observed_wind_from:.0f}°", f"from {cardinal(observed_wind_from)}"),
        kpi("Peak reading", f"{peak_reading:.2f}", f"threshold {alarm_threshold:.2f}",
            "red" if peak_reading >= alarm_threshold else ("amber" if peak_reading >= 0.5 * alarm_threshold else "green")),
    ])

    col1, col2, col3 = st.columns([1.15, 1.0, 1.1], gap="medium")
    with col1:
        md(scada_panel(readings, k_assim, alarm_threshold, (leak_x, leak_y)))
    with col2:
        md(wind_panel(wind_speed, wind_from, observed_wind_speed, observed_wind_from, result,
                      wind_speed_sd, wind_dir_sd))
    with col3:
        md(ci_panel(result, (leak_x, leak_y, strength, wind_speed, wind_from), latency_ms))

    live_mobile = ({"start": (mob_start_x, mob_start_y), "trail": [], "route_to": active_point}
                   if mobile_enabled else None)
    map_fig = draw_tactical_map(
        result, readings, k_assim, layers, alarm_threshold,
        truth=(leak_x, leak_y), active_point=active_point, baseline_xy=base_xy, mobile=live_mobile
    )
    md(hud(fig_img(map_fig, dpi=160), "TOPOGRAPHIC PROBABILITY MAP · FACILITY GRID 100 × 100 m",
           f"POSTERIOR AFTER {k_assim}/{N_SENSORS} READINGS · {n_particles:,} PARTICLES"))

    q_err_pct = 100.0 * abs(eq - strength) / max(strength, 1e-9)
    beat = error_m < base_err
    kpi_row([
        kpi("Location error*", f"{error_m:.1f} m", "twin estimate vs truth", "green" if beat else "amber"),
        kpi("Baseline error*", f"{base_err:.1f} m", "strongest-reading sensor"),
        kpi("Vs baseline*", f"{base_err - error_m:+.1f} m", "positive = twin is closer", "green" if beat else "red"),
        kpi("Release-rate error*", f"{q_err_pct:.0f}%", f"Q̂ {eq:.1f} vs {strength}"),
        kpi("Update latency", f"{latency_ms:.1f} ms", "single-frame inference",
            "green" if latency_ms < EDGE_LATENCY_TARGET_MS else "amber"),
        kpi("Effective particles", f"{result.ess:.0f}", "ESS after final update"),
    ])
    st.caption("*Only available because this is a simulation with known ground truth.")

    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown("### Predicted gas-dispersion heatmap")
        st.caption("Modelled concentration field for the simulated ground-truth scenario; this is a synthetic forecast, "
                   "not a measured gas map. Red line = alarm threshold.")
        disp_fig = draw_dispersion((leak_x, leak_y), strength, wind_speed, wind_from, alarm_threshold)
        md(hud(fig_img(disp_fig, dpi=140), "DISPERSION FORECAST", "GROUND TRUTH · RELATIVE UNITS"))
    with right:
        st.markdown("### Active-sensing recommendation (mobile sensor)")
        st.caption("Posterior-predictive variance heuristic over candidate positions the mobile sensor can reach "
                   "(not formal expected information gain).")
        info_fig = draw_info_map(active_grid, active_scores, active_point, (leak_x, leak_y), result)
        md(hud(fig_img(info_fig, dpi=140), "INFORMATION MAP", "BRIGHTER = MORE INFORMATIVE"))

    st.markdown("### Estimated state and uncertainty")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Estimated X", f"{ex:.1f} m", f"95%: {result.intervals['x_ci'][0]:.1f}–{result.intervals['x_ci'][1]:.1f}", delta_color="off")
    c2.metric("Estimated Y", f"{ey:.1f} m", f"95%: {result.intervals['y_ci'][0]:.1f}–{result.intervals['y_ci'][1]:.1f}", delta_color="off")
    c3.metric("Release Q", f"{eq:.1f}", f"95%: {result.intervals['q_ci'][0]:.1f}–{result.intervals['q_ci'][1]:.1f}", delta_color="off")
    c4.metric("Wind speed", f"{eu:.2f} m/s", f"95%: {result.intervals['u_ci'][0]:.2f}–{result.intervals['u_ci'][1]:.2f}", delta_color="off")
    c5.metric("Wind FROM", f"{etheta:.0f}°", "Circular estimate", delta_color="off")
    callout(
        f"Suggested next sensing point: <b>({active_point[0]:.1f}, {active_point[1]:.1f}) m</b>. "
        f"Predictive-variance score: {active_score:.3g}. This is a heuristic; it does not account for obstacles or flight safety.",
        "info",
    )

with tab_mobile:
    st.markdown("### Mobile sensing mission (stretch goal: where should the mobile sensor go next?)")
    st.write(
        "Closed loop: the mobile sensor starts at the chosen dock, the twin picks the most informative reachable waypoint, "
        "the sensor moves there, takes a noisy reading, and the particle filter assimilates it together with the four fixed "
        "sensors. Configure the mission in the sidebar (🛰 Mobile sensor)."
    )
    if not mobile_enabled:
        callout("Mobile sensor is switched off. Enable it in the sidebar under 🛰 Mobile sensor.", "warn")
    else:
        mission = run_mobile_mission(
            (leak_x, leak_y, strength, wind_speed, wind_from), readings,
            (observed_wind_speed, observed_wind_from), (wind_speed_sd, wind_dir_sd),
            (mob_start_x, mob_start_y), mob_steps, mob_max_step, mob_policy,
            n_particles=min(n_particles, 3000), noise_std=measurement_noise, seed=seed + 777,
        )
        render_mission_player(ctx, mission)
        frame = st.slider("Replay: state after mobile sample #", 0, len(mission) - 1, len(mission) - 1)
        h = mission[frame]
        trail = [(m["pos"][0], m["pos"][1], m["reading"]) for m in mission[1:frame + 1]]
        cur_pos = h["pos"]
        _, _, nxt, _ = active_sensing_scores(
            h["result"], h["coords"], measurement_noise, 17, origin=cur_pos, max_step=mob_max_step
        )
        first, last = mission[0], h
        improved = last["error"] < first["error"]
        step_ms = [m["latency_ms"] for m in mission[1:]] or [first["latency_ms"]]
        kpi_row([
            kpi("Fixed-only error*", f"{first['error']:.1f} m", f"CI width {first['ci_w']:.0f} m"),
            kpi(f"After {frame} mobile samples*", f"{last['error']:.1f} m", f"CI width {last['ci_w']:.0f} m",
                "green" if improved else "amber"),
            kpi("Error change*", f"{first['error'] - last['error']:+.1f} m", "positive = mobile sensor helped",
                "green" if improved else "red"),
            kpi("Policy", POLICY_LABELS[mob_policy].split(" (")[0], f"max {mob_max_step} m / sample", "blue"),
            kpi("Per-sample update", f"{max(step_ms):.0f} ms", "waypoint choice + inference (max)",
                "green" if max(step_ms) < HARD_LATENCY_BUDGET_MS else "red"),
        ])
        m_fig = draw_tactical_map(
            h["result"], readings, N_SENSORS, layers, alarm_threshold, truth=(leak_x, leak_y),
            active_point=nxt if frame < len(mission) - 1 or mob_policy == "active" else None,
            mobile={"start": (mob_start_x, mob_start_y), "trail": trail, "route_to": None}, figsize=(11.0, 6.9)
        )
        mc1, mc2 = st.columns([1.6, 1.0], gap="medium")
        with mc1:
            md(hud(fig_img(m_fig, dpi=140), "MOBILE MISSION MAP",
                   f"{POLICY_LABELS[mob_policy].upper()} · SAMPLE {frame}/{len(mission) - 1}"))
        with mc2:
            md(hud(fig_img(draw_mission_chart(mission, frame), dpi=120), "MISSION CONVERGENCE"))
            mdf = pd.DataFrame([{
                "Sample": m["step"], "Mobile X": round(m["pos"][0], 1), "Mobile Y": round(m["pos"][1], 1),
                "Reading": float("nan") if m["reading"] is None else round(m["reading"], 3),
                "Est X": round(m["result"].mean[0], 1), "Est Y": round(m["result"].mean[1], 1),
                "Error (m)*": round(m["error"], 2), "CI width (m)": round(m["ci_w"], 1),
                "Update (ms)": round(m["latency_ms"], 1),
            } for m in mission])
            show_df(mdf)
        st.caption("*Error vs truth is evaluation-only. Candidate waypoints are limited to the reach of one move, kept ≥ 6 m "
                   "from existing sensors, and chosen by posterior-predictive variance. No obstacle-aware routing.")
        if not improved and frame > 0:
            callout("In this scenario the mobile samples did not reduce error. Try another seed or policy, or run the "
                    "benchmark below for statistics over many scenarios.", "warn")

with tab_bench:
    st.markdown("### Reproducible synthetic validation")
    st.write(
        "The benchmark generates new hidden leak scenarios, gives the estimator sensor readings plus noisy wind telemetry, "
        "and compares its location estimate with a strongest-reading-sensor baseline."
    )
    bc1, bc2 = st.columns(2)
    with bc1:
        n_scenarios = st.selectbox("Number of scenarios (minimum requirement: 200)", [200, 300, 500], index=0)
    with bc2:
        bench_particles = st.selectbox("Particles per scenario", [500, 750, 1000, 1500], index=2)
    if st.button("Run benchmark", type="primary", key="run_benchmark"):
        bench_df, metrics = run_benchmark_live(
            ctx, n_scenarios, bench_particles, measurement_noise, seed + 10000
        )
        st.session_state["ps15_benchmark_df"] = bench_df
        st.session_state["ps15_benchmark_metrics"] = metrics

    if "ps15_benchmark_metrics" in st.session_state:
        metrics = st.session_state["ps15_benchmark_metrics"]
        bench_df = st.session_state["ps15_benchmark_df"]
        beats = metrics["improvement_pct"] > 0
        all_fast = metrics["within_2s_pct"] >= 100.0
        md("<div class='pill-row'>"
           + pill(f"COMPLETED {metrics['n']} SCENARIOS", "blue")
           + pill("TWIN BEATS BASELINE ON MEAN ERROR" if beats else "TWIN DID NOT BEAT BASELINE THIS RUN",
                  "green" if beats else "red")
           + pill("ALL UPDATES UNDER 2 s" if all_fast else f"{metrics['within_2s_pct']:.1f}% OF UPDATES UNDER 2 s",
                  "green" if all_fast else "amber")
           + "</div>")
        kpi_row([
            kpi("Twin mean error", f"{metrics['bayes_mean']:.2f} m", f"median {metrics['bayes_median']:.2f} · P95 {metrics['bayes_p95']:.2f}", "green"),
            kpi("Baseline mean error", f"{metrics['baseline_mean']:.2f} m", f"median {metrics['baseline_median']:.2f} · P95 {metrics['baseline_p95']:.2f}"),
            kpi("Mean error improvement", f"{metrics['improvement_pct']:.1f}%", "vs strongest-sensor baseline", "green" if beats else "red"),
            kpi("P95 update latency", f"{metrics['latency_p95']:.1f} ms", f"median {metrics['latency_median']:.1f} · max {metrics['latency_max']:.1f}", "blue"),
        ])
        kpi_row([
            kpi("X marginal coverage", f"{100 * metrics['x_coverage']:.1f}%", "nominal 95%"),
            kpi("Y marginal coverage", f"{100 * metrics['y_coverage']:.1f}%", "nominal 95%"),
            kpi("Joint X/Y coverage", f"{100 * metrics['joint_coverage']:.1f}%", "both inside intervals"),
            kpi("Updates under 2 seconds", f"{metrics['within_2s_pct']:.1f}%", f"mean Q error {metrics['q_rel_error_pct']:.1f}%"),
        ])
        ch1, ch2, ch3 = st.columns(3, gap="medium")
        with ch1:
            md(hud(fig_img(draw_bench_summary(metrics), dpi=130), "ERROR SUMMARY"))
        with ch2:
            md(hud(fig_img(draw_bench_cdf(bench_df), dpi=130), "ERROR DISTRIBUTION"))
        with ch3:
            md(hud(fig_img(draw_bench_coverage(metrics), dpi=130), "CALIBRATION"))
        show_df(bench_df)
        st.download_button(
            "Download benchmark CSV",
            data=bench_df.to_csv(index=False).encode("utf-8"),
            file_name=f"ps15_benchmark_{metrics['n']}_scenarios.csv",
            mime="text/csv",
        )
        if not all_fast:
            callout("The 2-second target was not met for every measured update on this run.", "warn")
        if not beats:
            callout("The twin did not beat the baseline in this run. Report this result honestly and improve the "
                    "model/experiment.", "warn")
        callout(
            "Coverage is an empirical diagnostic, not proof of calibration. This synthetic benchmark uses the same simplified "
            "plume family for data generation and inference; test model mismatch before making real-world claims.",
            "warn",
        )
    else:
        callout("Run the benchmark to populate the metrics. No performance values are pre-filled or fabricated.", "info")

    st.markdown("---")
    st.markdown("### Mobile active-sensing benchmark (stretch goal)")
    st.write(
        "Same hidden-leak setup, but a mobile sensor now takes samples. Compares **active sensing** with a **random walk**, "
        "a **chase-the-estimate** heuristic and the **fixed sensors only** (no mobile sensor), using identical noise. "
        "Per-sample latency includes waypoint selection."
    )
    mb1, mb2, mb3, mb4 = st.columns(4)
    with mb1:
        mb_n = st.selectbox("Mobile scenarios", [50, 100, 200], index=1)
    with mb2:
        mb_steps = st.selectbox("Samples per mission", [3, 4, 5, 6], index=1)
    with mb3:
        mb_particles = st.selectbox("Particles", [500, 750, 1000], index=1, key="mb_particles")
    with mb4:
        mb_move = st.selectbox("Max move / sample (m)", [20, 30, 40], index=1)
    if st.button("Run mobile-sensing benchmark", type="primary", key="run_mobile_benchmark"):
        mb_df, mb_sum = run_mobile_benchmark_live(
            ctx, mb_n, mb_particles, measurement_noise, seed + 20000, mb_steps, mb_move
        )
        st.session_state["ps15_mobile_df"], st.session_state["ps15_mobile_sum"] = mb_df, mb_sum
    if "ps15_mobile_sum" in st.session_state:
        ms_ = st.session_state["ps15_mobile_sum"]
        mdf_ = st.session_state["ps15_mobile_df"]
        win = ms_["active_vs_fixed_pct"] > 0
        kpi_row([
            kpi("Fixed sensors only", f"{ms_['fixed_mean']:.2f} m", "mean error, no mobile sensor"),
            kpi("Active sensing", f"{ms_['final_mean']['active']:.2f} m", f"after {ms_['steps']} samples · median {ms_['final_median']['active']:.2f}",
                "green" if win else "amber"),
            kpi("Random walk", f"{ms_['final_mean']['random']:.2f} m", f"median {ms_['final_median']['random']:.2f}"),
            kpi("Chase estimate", f"{ms_['final_mean']['chase']:.2f} m", f"median {ms_['final_median']['chase']:.2f}"),
            kpi("Active vs fixed", f"{ms_['active_vs_fixed_pct']:.1f}%", "mean error reduction", "green" if win else "red"),
            kpi("Active vs random", f"{ms_['active_vs_random_pct']:.1f}%", f"wins in {100 * ms_['active_win_rate_vs_random']:.0f}% of scenarios"),
            kpi("Per-sample latency", f"{ms_['lat_p95']:.0f} ms", f"P95 · max {ms_['lat_max']:.0f} ms · {ms_['within_2s_pct']:.0f}% < 2 s", "blue"),
        ])
        bm1, bm2 = st.columns([1, 1.4], gap="medium")
        with bm1:
            md(hud(fig_img(draw_mobile_bench(ms_), dpi=130), "ERROR VS MOBILE SAMPLES"))
        with bm2:
            show_df(mdf_)
            st.download_button("Download mobile benchmark CSV", data=mdf_.to_csv(index=False).encode("utf-8"),
                               file_name=f"ps15_mobile_benchmark_{ms_['n']}.csv", mime="text/csv")
        if not win:
            callout("Active sensing did not beat the fixed-only result in this run. Report this honestly.", "warn")
        callout("Synthetic result from the same simplified plume family used for inference; it shows the heuristic's behaviour, "
                "not field performance.", "warn")

with tab_lab:
    st.markdown("### What-if simulation laboratory")
    st.write("Change a scenario and compare the predicted sensor field. This does not modify the benchmark results.")
    a, b, c = st.columns(3)
    with a:
        lab_x = st.slider("What-if source X (m)", 0, 100, 50, key="labx")
        lab_y = st.slider("What-if source Y (m)", 0, 100, 50, key="laby")
    with b:
        lab_q = st.slider("What-if release Q", 10, 100, 80, key="labq")
        lab_u = st.slider("What-if wind speed (m/s)", 1.0, 10.0, 4.0, 0.5, key="labu")
    with c:
        lab_dir = st.slider("What-if wind FROM (°)", 0, 359, 225, key="labdir")
        lab_noise = st.slider("What-if noise", 0.05, 2.0, 0.2, 0.05, key="labnoise")
    lab_rng = np.random.default_rng(seed + 555)
    lab_readings = simulate_readings(
        lab_x, lab_y, lab_q, lab_u, lab_dir, SENSOR_XY, lab_rng,
        noise_std=lab_noise, offsets=SENSOR_OFFSETS
    )
    lab_start = time.perf_counter()
    lab_result = particle_filter_frame(
        SENSOR_XY, lab_readings, lab_u, lab_dir, n_particles=min(n_particles, 3000),
        noise_std=lab_noise, wind_speed_sd=wind_speed_sd, wind_dir_sd=wind_dir_sd,
        seed=seed + 556, offsets=SENSOR_OFFSETS
    )
    lab_latency = (time.perf_counter() - lab_start) * 1000.0
    lx, ly, lq, lu, ltheta = lab_result.mean
    lab_err = float(np.hypot(lx - lab_x, ly - lab_y))
    _, _, lab_active, _ = active_sensing_scores(lab_result, SENSOR_XY, noise_std=lab_noise)
    lab_base_err, lab_base_xy = nearest_sensor_baseline(SENSOR_XY, lab_readings, lab_x, lab_y)
    kpi_row([
        kpi("What-if estimated X", f"{lx:.1f} m", f"truth {lab_x} m", "green"),
        kpi("What-if estimated Y", f"{ly:.1f} m", f"truth {lab_y} m", "green"),
        kpi("What-if estimated Q", f"{lq:.1f}", f"truth {lab_q}"),
        kpi("Location error*", f"{lab_err:.1f} m", f"baseline {lab_base_err:.1f} m",
            "green" if lab_err < lab_base_err else "amber"),
        kpi("Update latency", f"{lab_latency:.1f} ms", "what-if inference", "blue"),
    ])
    lab_left, lab_right = st.columns([1.55, 1.0], gap="medium")
    with lab_left:
        lab_fig = draw_tactical_map(
            lab_result, lab_readings, N_SENSORS, layers, alarm_threshold, truth=(lab_x, lab_y),
            active_point=lab_active, baseline_xy=lab_base_xy, figsize=(10.0, 6.8)
        )
        md(hud(fig_img(lab_fig, dpi=140), "WHAT-IF TACTICAL MAP", "SEPARATE SYNTHETIC EXPERIMENT"))
    with lab_right:
        md(scada_panel(lab_readings, N_SENSORS, alarm_threshold, (lab_x, lab_y)))
    with st.expander("Raw what-if sensor data"):
        lab_df = pd.DataFrame({
            "Sensor": SENSOR_NAMES,
            "Simulated reading": np.round(lab_readings, 3),
            "X (m)": SENSOR_XY[:, 0],
            "Y (m)": SENSOR_XY[:, 1],
        })
        show_df(lab_df)
    st.caption("The what-if panel is a separate synthetic experiment, not evidence of field performance. "
               "*Evaluation-only because ground truth is known.")

st.markdown("---")
st.caption(
    "TECHNOVA 2026 · AEROSENSE AI . LIVE PROTOTYPE "

)
