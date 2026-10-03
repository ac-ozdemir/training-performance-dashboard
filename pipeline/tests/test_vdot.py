import pytest

from metrics.vdot import vdot


def test_known_value_5k_20min():
    # 5000m in 20:00 — golden value computed independently from the Daniels &
    # Gilbert formula (matches Daniels' published tables: VDOT 50 ≈ 5K in 19:57).
    assert vdot(distance_m=5000, duration_s=1200) == pytest.approx(49.806, rel=1e-4)


def test_known_value_10k_45min():
    assert vdot(distance_m=10000, duration_s=2700) == pytest.approx(45.263, rel=1e-4)


def test_faster_pace_gives_higher_vdot_same_duration():
    slower = vdot(distance_m=5000, duration_s=1500)
    faster = vdot(distance_m=6000, duration_s=1500)
    assert faster > slower


def test_faster_same_distance_gives_higher_vdot():
    slower = vdot(distance_m=5000, duration_s=1500)
    faster = vdot(distance_m=5000, duration_s=1200)
    assert faster > slower


@pytest.mark.parametrize(
    "bad_kwargs",
    [
        {"distance_m": 0, "duration_s": 1200},
        {"distance_m": -100, "duration_s": 1200},
        {"distance_m": 5000, "duration_s": 0},
        {"distance_m": 5000, "duration_s": -1},
    ],
)
def test_invalid_inputs_raise(bad_kwargs):
    with pytest.raises(ValueError):
        vdot(**bad_kwargs)
