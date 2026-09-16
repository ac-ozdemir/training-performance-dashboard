import pytest

from metrics.training_load import compute_daily_series, next_atl, next_ctl


def test_first_day_tsb_is_zero_from_fresh_start():
    rows = compute_daily_series([100], initial_ctl=0.0, initial_atl=0.0)
    assert rows[0]["tsb"] == 0.0
    assert rows[0]["ctl"] == pytest.approx(2.380952, rel=1e-5)
    assert rows[0]["atl"] == pytest.approx(14.285714, rel=1e-5)


def test_second_day_tsb_reflects_previous_day_fatigue():
    rows = compute_daily_series([100, 0], initial_ctl=0.0, initial_atl=0.0)
    # after a big day-1 load, atl has risen faster than ctl -> negative form
    assert rows[1]["tsb"] == pytest.approx(-11.904762, rel=1e-5)


def test_constant_load_converges_towards_itself():
    rows = compute_daily_series([50.0] * 300)
    last = rows[-1]
    assert last["ctl"] == pytest.approx(50.0, abs=0.1)
    assert last["atl"] == pytest.approx(50.0, abs=0.01)
    assert last["tsb"] == pytest.approx(0.0, abs=0.1)


def test_taper_produces_positive_tsb():
    # four weeks of steady loading, then a week of rest -> form should turn positive
    loads = [80.0] * 28 + [0.0] * 7
    rows = compute_daily_series(loads)
    assert rows[-1]["tsb"] > 0


def test_rest_days_are_zero_load_and_decay_both():
    rows = compute_daily_series([0.0, 0.0, 0.0], initial_ctl=40.0, initial_atl=40.0)
    for row in rows:
        assert row["ctl"] < 40.0
        assert row["atl"] < 40.0
    # atl (7-day constant) decays faster than ctl (42-day constant)
    assert rows[-1]["atl"] < rows[-1]["ctl"]


def test_next_ctl_and_next_atl_time_constants():
    assert next_ctl(prev_ctl=0.0, todays_load=42.0) == pytest.approx(1.0)
    assert next_atl(prev_atl=0.0, todays_load=7.0) == pytest.approx(1.0)


def test_series_length_matches_input():
    rows = compute_daily_series([10.0, 20.0, 0.0, 5.0])
    assert len(rows) == 4
