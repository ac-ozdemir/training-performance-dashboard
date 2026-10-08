"""List past runs that would add a VDOT point if tagged "Workout" in Strava.

Fetches laps for heart-rate runs since LOAD_SERIES_START that are not already tagged
Workout or Race, then applies the interval and tempo rules from metrics/workouts.py.
Also reports lapped structures that miss only the effort threshold. Uses the pipeline's
own Secret Manager credentials so a rotated Strava refresh token is stored back, never
left out of sync with the nightly function.

Usage (from pipeline/): .venv/bin/python -m analysis.find_workout_candidates
"""

import truststore

truststore.inject_into_ssl()

import time  # noqa: E402

import requests  # noqa: E402
from google.cloud import bigquery  # noqa: E402

from config import (  # noqa: E402
    ACTIVITIES_TABLE,
    ATHLETE,
    LOAD_SERIES_START,
    SECRET_CLIENT_ID,
    SECRET_CLIENT_SECRET,
    SECRET_REFRESH_TOKEN,
)
from metrics.workouts import (  # noqa: E402
    interval_vdot,
    select_tempo_blocks,
    select_work_laps,
    tempo_vdot,
)
from secrets_store import SecretStore  # noqa: E402
from strava.client import StravaClient  # noqa: E402
from strava.transform import RACE_WORKOUT_TYPE, WORKOUT_WORKOUT_TYPE, to_lap_row  # noqa: E402

# Strava allows 100 read requests per 15 minutes; spread the scan to stay under it.
SECONDS_BETWEEN_CALLS = 12.0
RATE_LIMIT_WAIT_SECONDS = 60


def laps_for(strava: StravaClient, activity_id: str) -> list[dict]:
    """Fetch laps, waiting out a full rate-limit window instead of failing the scan."""
    while True:
        try:
            return [to_lap_row(lap) for lap in strava.list_laps(activity_id)]
        except requests.HTTPError as error:
            if error.response is None or error.response.status_code != 429:
                raise
            print(f"(rate limited, waiting {RATE_LIMIT_WAIT_SECONDS}s)", flush=True)
            time.sleep(RATE_LIMIT_WAIT_SECONDS)


def candidate_runs() -> list[dict]:
    query = f"""
        SELECT activity_id, name, DATE(start_date_local) AS day, distance_m
        FROM `{ACTIVITIES_TABLE}`
        WHERE category = 'run' AND has_heartrate
          AND DATE(start_date_local) >= '{LOAD_SERIES_START}'
          AND IFNULL(workout_type, 0) NOT IN ({RACE_WORKOUT_TYPE}, {WORKOUT_WORKOUT_TYPE})
        ORDER BY day
    """
    return [dict(row) for row in bigquery.Client().query(query).result()]


def pace(speed: float) -> str:
    seconds = round(1000 / speed)
    return f"{seconds // 60}:{seconds % 60:02d}"


def describe(laps: list[dict]) -> str:
    return f"{len(laps)} × " + ", ".join(
        f"{round(lap['moving_time_s'] / 60, 1)} min @ {pace(lap['average_speed'])}"
        f" (HR {round(lap.get('average_heartrate') or 0)})"
        for lap in laps
    )


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
    print(f"Checking {len(runs)} untagged heart-rate runs since {LOAD_SERIES_START}...\n")
    qualifying, too_easy = [], []
    for run in runs:
        laps = laps_for(strava, run["activity_id"])
        time.sleep(SECONDS_BETWEEN_CALLS)
        head = f"{run['day']} | {run['name']} | {round(run['distance_m'] / 1000, 1)} km"
        for kind, select, score in (
            ("interval", select_work_laps, interval_vdot),
            ("tempo", select_tempo_blocks, tempo_vdot),
        ):
            work = select(laps)
            if not work:
                continue
            value = score(laps, ATHLETE)
            line = f"{head} | {kind}: {describe(work)}"
            if value is not None:
                qualifying.append(f"{line} | VDOT {value:.1f}")
            else:
                too_easy.append(line)
            break

    print("Would add a VDOT point if tagged 'Workout':")
    print("\n".join(f"- {line}" for line in qualifying) or "- none")
    print("\nLapped interval/tempo structure, but below the effort threshold:")
    print("\n".join(f"- {line}" for line in too_easy) or "- none")


if __name__ == "__main__":
    main()
