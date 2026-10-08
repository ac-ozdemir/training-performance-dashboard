"""Pure mapping from raw Strava payloads to warehouse rows. GPS/route fields never leave here."""

from datetime import datetime

RUN_TYPES = frozenset({"Run", "TrailRun", "VirtualRun"})
CROSSFIT_TYPES = frozenset(
    {"HighIntensityIntervalTraining", "Workout", "WeightTraining", "Crossfit"}
)
# Strava run types the athlete sets per activity ("Run type" when editing a run).
RACE_WORKOUT_TYPE = 1
WORKOUT_WORKOUT_TYPE = 3


def category_for(sport_type: str) -> str:
    if sport_type in RUN_TYPES:
        return "run"
    if sport_type in CROSSFIT_TYPES:
        return "crossfit"
    return "other"


def is_workout_session(activity: dict) -> bool:
    """A run the athlete tagged as "Workout" in Strava (intervals or tempo)."""
    return (
        activity.get("sport_type") in RUN_TYPES
        and activity.get("workout_type") == WORKOUT_WORKOUT_TYPE
    )


def _local_datetime(value: str) -> str:
    # Strava suffixes start_date_local with "Z" even though it is wall-clock local time.
    return value.removesuffix("Z")


def to_lap_row(lap: dict) -> dict:
    return {
        "lap_index": lap.get("lap_index"),
        "distance_m": lap.get("distance"),
        "moving_time_s": lap.get("moving_time"),
        "average_speed": lap.get("average_speed"),
        "average_heartrate": lap.get("average_heartrate"),
    }


def to_activity_row(activity: dict, ingested_at: datetime, laps: list[dict]) -> dict:
    return {
        "activity_id": str(activity["id"]),
        "athlete_id": str(activity["athlete"]["id"]),
        "name": activity.get("name"),
        "sport_type": activity.get("sport_type"),
        "workout_type": activity.get("workout_type"),
        "category": category_for(activity.get("sport_type", "")),
        "start_date": activity["start_date"],
        "start_date_local": _local_datetime(activity["start_date_local"]),
        "timezone": activity.get("timezone"),
        "elapsed_time_s": activity.get("elapsed_time"),
        "moving_time_s": activity.get("moving_time"),
        "distance_m": activity.get("distance"),
        "has_heartrate": bool(activity.get("has_heartrate")),
        "average_heartrate": activity.get("average_heartrate"),
        "max_heartrate": activity.get("max_heartrate"),
        "average_speed": activity.get("average_speed"),
        "max_speed": activity.get("max_speed"),
        "total_elevation_gain": activity.get("total_elevation_gain"),
        "suffer_score": activity.get("suffer_score"),
        "laps": laps,
        "ingested_at": ingested_at.isoformat(),
    }
