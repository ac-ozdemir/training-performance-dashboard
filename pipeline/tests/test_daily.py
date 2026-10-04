from datetime import date

import pytest

from config import AthleteParams
from metrics.daily import activity_trimp, activity_vdot, build_daily_metrics
from metrics.vdot import vdot

ATHLETE = AthleteParams(resting_hr=48, max_hr=185, lthr=165, sex="male")
EARLY = date(2000, 1, 1)


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


def _build(rows: list[dict], today: date, load_start: date = EARLY) -> list[dict]:
    return build_daily_metrics(rows, ATHLETE, today=today, load_start=load_start)


def test_no_heart_rate_means_no_trimp():
    assert activity_trimp(_row("2026-10-01", average_heartrate=None), ATHLETE) is None


def test_rest_days_are_filled_with_zero_load():
    daily = _build([_row("2026-10-01"), _row("2026-10-04")], today=date(2026, 10, 5))
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
    day = _build(rows, today=date(2026, 10, 1))[0]
    assert day["trimp_run"] > 0
    assert day["trimp_crossfit"] > 0
    assert day["trimp_other"] == 0.0
    assert day["daily_trimp"] == pytest.approx(day["trimp_run"] + day["trimp_crossfit"])


def test_load_series_starts_at_load_start_and_is_seeded():
    rows = [_row("2026-09-01")] + [_row(f"2026-10-{d:02d}") for d in range(1, 6)]
    daily = _build(rows, today=date(2026, 10, 5), load_start=date(2026, 10, 1))
    before = [d for d in daily if d["date"] < "2026-10-01"]
    after = [d for d in daily if d["date"] >= "2026-10-01"]
    assert all(d["ctl"] is None and d["tsb"] is None for d in before)
    assert before[0]["daily_trimp"] > 0  # TRIMP itself is still recorded
    # seeded with the period's mean load rather than ramping up from zero
    assert after[0]["ctl"] == pytest.approx(after[0]["daily_trimp"], rel=0.05)


def test_race_uses_elapsed_time():
    race = _row("2025-11-02", workout_type=1, distance_m=42195.0, elapsed_time_s=12600)
    value, source = activity_vdot(race, ATHLETE)
    assert source == "race"
    assert value == pytest.approx(vdot(42195.0, 12600))
    assert value == pytest.approx(44.5, abs=0.2)  # 3:30 marathon


def test_easy_runs_and_crossfit_have_no_vdot():
    assert activity_vdot(_row("2026-10-01"), ATHLETE) is None
    assert activity_vdot(_row("2026-10-01", category="crossfit", workout_type=1), ATHLETE) is None


def test_race_beats_interval_on_same_day():
    rep = {
        "average_speed": 4.17,
        "moving_time_s": 180,
        "distance_m": 750.0,
        "average_heartrate": 158,
    }
    jog = {"average_speed": 2.5, "moving_time_s": 90, "distance_m": 225.0, "average_heartrate": 145}
    rows = [
        _row("2026-10-01", laps=[rep, jog, rep, jog, rep]),
        _row("2026-10-01", workout_type=1, distance_m=5000.0, elapsed_time_s=1200),
    ]
    day = _build(rows, today=date(2026, 10, 1))[0]
    assert day["vdot_source"] == "race"


def test_empty_input():
    assert _build([], today=date(2026, 10, 1)) == []
