from datetime import UTC, date, datetime

from config import ATHLETE
from export.dashboard import build_payload
from metrics.daily import build_daily_metrics


def _row(day: str, name: str, category: str = "run", **overrides) -> dict:
    row = {
        "activity_id": "1",
        "name": name,
        "sport_type": "Run" if category == "run" else "HighIntensityIntervalTraining",
        "category": category,
        "workout_type": None,
        "start_date_local": f"{day}T08:00:00",
        "moving_time_s": 3000,
        "elapsed_time_s": 3100,
        "distance_m": 10000.0,
        "average_heartrate": 150.0,
        "laps": [],
    }
    row.update(overrides)
    return row


def _payload(rows: list[dict]) -> dict:
    daily = build_daily_metrics(rows, ATHLETE, today=date(2026, 10, 5))
    return build_payload(rows, daily, generated_at=datetime(2026, 10, 5, tzinfo=UTC))


def test_activity_names_and_ids_are_not_published():
    rows = [_row("2026-10-01", "Birthday Run at Home Street"), _row("2026-10-02", "Evening HIIT")]
    payload = _payload(rows)
    text = str(payload)
    assert "Birthday" not in text
    assert "Home Street" not in text
    assert all("name" not in a and "activity_id" not in a for a in payload["activities"])


def test_race_name_is_kept_only_as_vdot_label():
    rows = [
        _row(
            "2025-11-02",
            "Istanbul Marathon 2025",
            workout_type=1,
            distance_m=42195.0,
            elapsed_time_s=12600,
        )
    ]
    payload = _payload(rows)
    assert payload["vdot"] == [
        {"date": "2025-11-02", "vdot": 44.6, "source": "race", "label": "Istanbul Marathon 2025"}
    ]


def test_pace_only_for_runs_and_attribution_present():
    rows = [_row("2026-10-01", "Run"), _row("2026-10-01", "HIIT", category="crossfit")]
    payload = _payload(rows)
    run, hiit = sorted(payload["activities"], key=lambda a: a["category"], reverse=True)
    assert run["pace_min_per_km"] == 5.0
    assert hiit["pace_min_per_km"] is None
    assert "Strava" in payload["attribution"]
