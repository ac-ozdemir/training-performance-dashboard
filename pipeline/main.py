"""Cloud Function entry point: Strava -> BigQuery -> daily metrics -> public dashboard.json."""

import json
import sys
import traceback
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import functions_framework
from google.cloud import bigquery

from config import (
    ACTIVITIES_TABLE,
    ATHLETE,
    LOAD_SERIES_START,
    METRICS_TABLE,
    SECRET_CLIENT_ID,
    SECRET_CLIENT_SECRET,
    SECRET_REFRESH_TOKEN,
)
from export.dashboard import build_payload, publish
from metrics.daily import build_daily_metrics
from secrets_store import SecretStore
from strava.client import StravaClient
from strava.transform import is_workout_session, to_activity_row, to_lap_row
from warehouse.bigquery import existing_laps, replace_table

LOCAL_TZ = ZoneInfo("Europe/Istanbul")


def log(severity: str, message: str, **fields) -> None:
    # Cloud Logging parses one JSON object per stdout line into a structured entry.
    print(json.dumps({"severity": severity, "message": message, **fields}), file=sys.stdout)


def run() -> dict:
    secrets = SecretStore()
    strava = StravaClient(
        client_id=secrets.get(SECRET_CLIENT_ID),
        client_secret=secrets.get(SECRET_CLIENT_SECRET),
        refresh_token=secrets.get(SECRET_REFRESH_TOKEN),
    )
    if strava.authenticate():
        secrets.replace(SECRET_REFRESH_TOKEN, strava.refresh_token)
        log("INFO", "Strava refresh token rotated and stored")

    activities = strava.list_activities()
    bq = bigquery.Client()
    known_laps = existing_laps(bq)

    now = datetime.now(UTC)
    rows, laps_fetched = [], 0
    for activity in activities:
        activity_id = str(activity["id"])
        laps = known_laps.get(activity_id, [])
        if not laps and is_workout_session(activity):
            laps = [to_lap_row(lap) for lap in strava.list_laps(activity_id)]
            laps_fetched += 1
        rows.append(to_activity_row(activity, ingested_at=now, laps=laps))

    replace_table(bq, ACTIVITIES_TABLE, rows)

    daily = build_daily_metrics(
        rows, ATHLETE, today=now.astimezone(LOCAL_TZ).date(), load_start=LOAD_SERIES_START
    )
    computed_at = now.isoformat()
    replace_table(bq, METRICS_TABLE, [{**day, "computed_at": computed_at} for day in daily])

    url = publish(build_payload(rows, daily, generated_at=now))

    summary = {
        "activities": len(rows),
        "laps_fetched": laps_fetched,
        "metric_days": len(daily),
        "export_url": url,
    }
    log("INFO", "Pipeline run finished", **summary)
    return summary


@functions_framework.http
def daily_pipeline(request):
    try:
        run()
    except Exception as error:
        log("ERROR", "Pipeline run failed", error=repr(error), trace=traceback.format_exc())
        return ("Pipeline run failed", 500)
    return ("OK", 200)
