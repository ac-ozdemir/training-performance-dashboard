"""Build and publish the public, pre-aggregated dashboard.json consumed by the portfolio site.

Only aggregate numbers leave the warehouse: no activity names (they can reveal locations or
personal details), no ids, no GPS. Race names are kept on VDOT points since races are public
events.
"""

import json
from datetime import datetime

from google.cloud import storage

from config import ATHLETE, EXPORT_BUCKET, EXPORT_OBJECT
from metrics.daily import activity_date, activity_trimp

SCHEMA_VERSION = 1


def _round(value: float | None, digits: int = 1) -> float | None:
    return None if value is None else round(value, digits)


def _activity_summary(row: dict) -> dict:
    distance_km = (row.get("distance_m") or 0) / 1000
    moving_min = (row.get("moving_time_s") or 0) / 60
    pace = moving_min / distance_km if row["category"] == "run" and distance_km > 0 else None
    return {
        "date": activity_date(row).isoformat(),
        "category": row["category"],
        "sport_type": row["sport_type"],
        "distance_km": _round(distance_km, 2),
        "moving_time_min": _round(moving_min),
        "pace_min_per_km": _round(pace, 2),
        "avg_hr": _round(row.get("average_heartrate")),
        "trimp": _round(activity_trimp(row, ATHLETE)),
    }


def build_payload(rows: list[dict], daily: list[dict], generated_at: datetime) -> dict:
    race_names = {
        activity_date(row).isoformat(): row["name"]
        for row in rows
        if row["category"] == "run" and row.get("workout_type") == 1
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at.isoformat(),
        "attribution": "Data provided by Strava. Powered by Strava.",
        "daily": [
            {
                "date": day["date"],
                "trimp": _round(day["daily_trimp"]),
                "trimp_run": _round(day["trimp_run"]),
                "trimp_crossfit": _round(day["trimp_crossfit"]),
                "trimp_other": _round(day["trimp_other"]),
                "ctl": _round(day["ctl"]),
                "atl": _round(day["atl"]),
                "tsb": _round(day["tsb"]),
            }
            for day in daily
            if day["ctl"] is not None
        ],
        "vdot": [
            {
                "date": day["date"],
                "vdot": _round(day["vdot"]),
                "source": day["vdot_source"],
                "label": race_names.get(day["date"]) if day["vdot_source"] == "race" else None,
            }
            for day in daily
            if day["vdot"] is not None
        ],
        "activities": sorted((_activity_summary(row) for row in rows), key=lambda a: a["date"]),
    }


def publish(payload: dict, client: storage.Client | None = None) -> str:
    client = client or storage.Client()
    blob = client.bucket(EXPORT_BUCKET).blob(EXPORT_OBJECT)
    blob.cache_control = "public, max-age=3600"
    blob.upload_from_string(
        json.dumps(payload, ensure_ascii=False), content_type="application/json"
    )
    return f"https://storage.googleapis.com/{EXPORT_BUCKET}/{EXPORT_OBJECT}"
