"""List past runs that would qualify as interval sessions if titled "interval".

Fetches laps for heart-rate runs since LOAD_SERIES_START that are not already titled
"interval" or tagged as races, then applies the same rules as metrics/intervals.py.
Uses the pipeline's own Secret Manager credentials so a rotated Strava refresh token is
stored back, never left out of sync with the nightly function.

Usage (from pipeline/): .venv/bin/python -m analysis.find_interval_candidates
"""

import truststore

truststore.inject_into_ssl()

import time  # noqa: E402

from google.cloud import bigquery  # noqa: E402

from config import (  # noqa: E402
    ACTIVITIES_TABLE,
    ATHLETE,
    INTERVAL_KEYWORD,
    LOAD_SERIES_START,
    SECRET_CLIENT_ID,
    SECRET_CLIENT_SECRET,
    SECRET_REFRESH_TOKEN,
)
from metrics.intervals import (  # noqa: E402
    MIN_REP_HR_SHARE_OF_LTHR,
    is_auto_lapped,
    select_work_laps,
    session_vdot,
)
from secrets_store import SecretStore  # noqa: E402
from strava.client import StravaClient  # noqa: E402
from strava.transform import RACE_WORKOUT_TYPE, to_lap_row  # noqa: E402

# Strava allows 100 read requests per 15 minutes; stay well under it.
SECONDS_BETWEEN_CALLS = 1.0


def candidate_runs() -> list[dict]:
    query = f"""
        SELECT activity_id, name, DATE(start_date_local) AS day, distance_m
        FROM `{ACTIVITIES_TABLE}`
        WHERE category = 'run' AND has_heartrate
          AND DATE(start_date_local) >= '{LOAD_SERIES_START}'
          AND NOT CONTAINS_SUBSTR(name, '{INTERVAL_KEYWORD}')
          AND IFNULL(workout_type, 0) != {RACE_WORKOUT_TYPE}
        ORDER BY day
    """
    return [dict(row) for row in bigquery.Client().query(query).result()]


def pace(speed: float) -> str:
    seconds = round(1000 / speed)
    return f"{seconds // 60}:{seconds % 60:02d}"


def main() -> None:
    secrets = SecretStore()
    strava = StravaClient(
        secrets.get(SECRET_CLIENT_ID),
        secrets.get(SECRET_CLIENT_SECRET),
        secrets.get(SECRET_REFRESH_TOKEN),
    )
    if strava.authenticate():
        secrets.replace(SECRET_REFRESH_TOKEN, strava.refresh_token)
        print("(refresh token rotated and stored in Secret Manager)")

    runs = candidate_runs()
    print(f"Checking {len(runs)} heart-rate runs since {LOAD_SERIES_START}...\n")
    min_hr = ATHLETE.lthr * MIN_REP_HR_SHARE_OF_LTHR
    qualifying, structured = [], []
    for run in runs:
        laps = [to_lap_row(lap) for lap in strava.list_laps(run["activity_id"])]
        time.sleep(SECONDS_BETWEEN_CALLS)
        if is_auto_lapped(laps):
            continue
        reps = select_work_laps(laps)
        if not reps:
            continue
        hard = [lap for lap in reps if (lap.get("average_heartrate") or 0) >= min_hr]
        summary = (
            f"{run['day']} | {run['name']} | {round(run['distance_m'] / 1000, 1)} km | "
            f"{len(reps)} reps @ {', '.join(pace(lap['average_speed']) for lap in reps)} /km | "
            f"rep HR {', '.join(str(round(lap.get('average_heartrate') or 0)) for lap in reps)}"
        )
        value = session_vdot(laps, ATHLETE)
        if value is not None:
            qualifying.append(f"{summary} | {len(hard)} at ≥{min_hr:.0f} bpm | VDOT {value:.1f}")
        else:
            structured.append(f"{summary} | too easy for VO2max reps")

    print("Would add a VDOT point if titled 'interval':")
    print("\n".join(f"- {line}" for line in qualifying) or "- none")
    print("\nManually lapped rep structure, but below the effort threshold:")
    print("\n".join(f"- {line}" for line in structured) or "- none")


if __name__ == "__main__":
    main()
