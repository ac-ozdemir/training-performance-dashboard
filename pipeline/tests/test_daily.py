from datetime import date

import pytest

from config import AthleteParams
from metrics.daily import activity_trimp, activity_vdot, build_daily_metrics
from metrics.vdot import vdot

ATHLETE = AthleteParams(resting_hr=48, max_hr=185, sex="male")


def _row(day: str, category: str = "run", **overrides) -> dict:
    row = {
        "start_date_local": f"{day}T08:00:00",
        "category": category,
        "workout_type": None,
        "moving_time_s": 3600,
        "elapsed_time_s": 3700,
        "distance_m": 10000.0,
        "average_heartrate": 150.0,
        "laps": [],
    }
    row.update(overrides)
    return row


def test_no_heart_rate_means_no_trimp():
    assert activity_trimp(_row("2026-10-01", average_heartrate=None), ATHLETE) is None


def test_rest_days_are_filled_with_zero_load():
    rows = [_row("2026-10-01"), _row("2026-10-04")]
    daily = build_daily_metrics(rows, ATHLETE, today=date(2026, 10, 5))
    assert [d["date"] for d in daily] == [
        "2026-10-01",
        "2026-10-02",
        "2026-10-03",
        "2026-10-04",
        "2026-10-05",
    ]
    assert daily[1]["daily_trimp"] == 0.0
    assert daily[0]["daily_trimp"] > 0


def test_load_is_split_by_category_and_summed():
    rows = [_row("2026-10-01"), _row("2026-10-01", category="crossfit", moving_time_s=2400)]
    day = build_daily_metrics(rows, ATHLETE, today=date(2026, 10, 1))[0]
    assert day["trimp_run"] > 0
    assert day["trimp_crossfit"] > 0
    assert day["trimp_other"] == 0.0
    assert day["daily_trimp"] == pytest.approx(day["trimp_run"] + day["trimp_crossfit"])


def test_race_uses_elapsed_time():
    race = _row("2025-11-02", workout_type=1, distance_m=42195.0, elapsed_time_s=12600)
    value, source = activity_vdot(race)
    assert source == "race"
    assert value == pytest.approx(vdot(42195.0, 12600))
    assert value == pytest.approx(44.5, abs=0.2)  # 3:30 marathon


def test_easy_runs_and_crossfit_have_no_vdot():
    assert activity_vdot(_row("2026-10-01")) is None
    assert activity_vdot(_row("2026-10-01", category="crossfit", workout_type=1)) is None


def test_race_beats_interval_on_same_day():
    laps = [
        {"average_speed": 2.78, "moving_time_s": 360},
        {"average_speed": 4.17, "moving_time_s": 240},
        {"average_speed": 2.5, "moving_time_s": 120},
        {"average_speed": 4.17, "moving_time_s": 240},
    ]
    rows = [
        _row("2026-10-01", laps=laps),
        _row("2026-10-01", workout_type=1, distance_m=5000.0, elapsed_time_s=1200),
    ]
    day = build_daily_metrics(rows, ATHLETE, today=date(2026, 10, 1))[0]
    assert day["vdot_source"] == "race"


def test_empty_input():
    assert build_daily_metrics([], ATHLETE, today=date(2026, 10, 1)) == []
