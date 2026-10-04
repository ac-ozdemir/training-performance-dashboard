"""Runtime config: GCP resource names (env-overridable) and personal physiology parameters."""

import os
from dataclasses import dataclass
from datetime import date

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "training-performance-dashboard")
DATASET = os.environ.get("BQ_DATASET", "training_performance")
ACTIVITIES_TABLE = f"{PROJECT_ID}.{DATASET}.activities"
METRICS_TABLE = f"{PROJECT_ID}.{DATASET}.metrics"

EXPORT_BUCKET = os.environ.get("EXPORT_BUCKET", "training-performance-dashboard-public")
EXPORT_OBJECT = "dashboard.json"

SECRET_CLIENT_ID = "strava-client-id"
SECRET_CLIENT_SECRET = "strava-client-secret"
SECRET_REFRESH_TOKEN = "strava-refresh-token"

INTERVAL_KEYWORD = "interval"


@dataclass(frozen=True)
class AthleteParams:
    resting_hr: float
    max_hr: float
    lthr: float
    sex: str


# Resting HR: Garmin 1-year average. Max HR: highest plausible value observed in Strava data
# (a single 210 bpm reading on a HIIT session was treated as an optical sensor spike).
# LTHR: field test, October 2026.
ATHLETE = AthleteParams(resting_hr=48, max_hr=185, lthr=165, sex="male")

# Heart-rate data is only consistently recorded from this date on; before it, training load
# would read as near-zero, so the CTL/ATL/TSB series starts here.
LOAD_SERIES_START = date(2025, 11, 1)
