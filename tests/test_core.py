import numpy as np

from twin.config import SENSOR_OFFSETS, SENSOR_XY
from twin.inference import active_sensing_scores, particle_filter_frame
from twin.physics import gaussian_plume, simulate_readings


def test_plume_is_zero_upwind_and_positive_downwind():
    # wind FROM the south (180 deg) blows toward the north: a point north of the source is downwind
    down = gaussian_plume(50.0, 70.0, 50.0, 50.0, 80.0, 3.0, 180.0)
    up = gaussian_plume(50.0, 30.0, 50.0, 50.0, 80.0, 3.0, 180.0)
    assert float(down) > 0.0
    assert float(up) == 0.0


def test_readings_are_non_negative_and_seeded():
    a = simulate_readings(55, 55, 90, 3.5, 225, SENSOR_XY, np.random.default_rng(1), 0.2, SENSOR_OFFSETS)
    b = simulate_readings(55, 55, 90, 3.5, 225, SENSOR_XY, np.random.default_rng(1), 0.2, SENSOR_OFFSETS)
    assert np.all(a >= 0) and np.allclose(a, b)


def test_particle_filter_beats_strongest_sensor_on_average():
    rng = np.random.default_rng(7)
    twin, base = [], []
    for i in range(12):
        tx, ty = rng.uniform(20, 80, 2)
        obs = simulate_readings(tx, ty, 80, 3.0, 225, SENSOR_XY, rng, 0.2, SENSOR_OFFSETS)
        res = particle_filter_frame(SENSOR_XY, obs, 3.0, 225, n_particles=1500, noise_std=0.2,
                                    wind_speed_sd=0.7, wind_dir_sd=18.0, seed=i, offsets=SENSOR_OFFSETS)
        twin.append(np.hypot(res.mean[0] - tx, res.mean[1] - ty))
        b = SENSOR_XY[int(np.argmax(obs))]
        base.append(np.hypot(b[0] - tx, b[1] - ty))
        assert res.ess > 1.0 and abs(res.weights.sum() - 1.0) < 1e-6
    assert np.mean(twin) < np.mean(base)


def test_active_sensing_respects_reach_and_spacing():
    obs = simulate_readings(55, 55, 90, 3.5, 225, SENSOR_XY, np.random.default_rng(3), 0.2, SENSOR_OFFSETS)
    res = particle_filter_frame(SENSOR_XY, obs, 3.5, 225, n_particles=1500, noise_std=0.2,
                                wind_speed_sd=0.7, wind_dir_sd=18.0, seed=3, offsets=SENSOR_OFFSETS)
    _, _, pt, _ = active_sensing_scores(res, SENSOR_XY, 0.2, origin=(50, 8), max_step=30)
    assert np.hypot(pt[0] - 50, pt[1] - 8) <= 30 + 1e-6
    assert np.min(np.hypot(SENSOR_XY[:, 0] - pt[0], SENSOR_XY[:, 1] - pt[1])) >= 6.0
