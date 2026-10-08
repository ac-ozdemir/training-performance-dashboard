from datetime import UTC, datetime

import pytest

from strava.transform import category_for, is_workout_session, to_activity_row

INGESTED_AT = datetime(2026, 10, 4, 20, 0, tzinfo=UTC)


def _activity(**overrides) -> dict:
    activity = {
        "id": 123,
        "athlete": {"id": 456},
        "name": "Evening Run",
        "sport_type": "Run",
        "workout_type": None,
        "start_date": "2026-10-04T16:00:00Z",
        "start_date_local": "2026-10-04T19:00:00Z",
        "timezone": "(GMT+03:00) Europe/Istanbul",
        "elapsed_time": 3000,
        "moving_time": 2900,
        "distance": 10000.0,
        "has_heartrate": True,
        "average_heartrate": 150.0,
        "max_heartrate": 170.0,
        "average_speed": 3.45,
        "max_speed": 4.5,
        "total_elevation_gain": 40.0,
        "start_latlng": [39.9, 32.8],
        "end_latlng": [39.9, 32.8],
        "map": {"summary_polyline": "abc"},
    }
    activity.update(overrides)
    return activity


def test_gps_and_route_fields_never_reach_the_row():
    row = to_activity_row(_activity(), INGESTED_AT, laps=[])
    assert not {"start_latlng", "end_latlng", "map"} & row.keys()
    assert "abc" not in str(row)


def test_local_start_time_drops_misleading_utc_suffix():
    row = to_activity_row(_activity(), INGESTED_AT, laps=[])
    assert row["start_date_local"] == "2026-10-04T19:00:00"
    assert row["start_date"] == "2026-10-04T16:00:00Z"


def test_ids_are_strings_and_missing_heart_rate_is_none():
    row = to_activity_row(
        _activity(has_heartrate=False, average_heartrate=None), INGESTED_AT, laps=[]
    )
    assert row["activity_id"] == "123"
    assert row["athlete_id"] == "456"
    assert row["has_heartrate"] is False
    assert row["average_heartrate"] is None


@pytest.mark.parametrize(
    ("sport_type", "expected"),
    [
        ("Run", "run"),
        ("TrailRun", "run"),
        ("HighIntensityIntervalTraining", "crossfit"),
        ("Workout", "crossfit"),
        ("WeightTraining", "crossfit"),
        ("Hike", "other"),
        ("Swim", "other"),
    ],
)
def test_category_mapping(sport_type, expected):
    assert category_for(sport_type) == expected


def test_workout_sessions_come_from_the_strava_run_type_not_the_title():
    assert is_workout_session(_activity(name="Evening Run", workout_type=3))
    assert not is_workout_session(_activity(name="Interval Friday", workout_type=None))
    assert not is_workout_session(_activity(name="Runtalya 2026", workout_type=1))
    assert not is_workout_session(
        _activity(sport_type="HighIntensityIntervalTraining", workout_type=3)
    )
