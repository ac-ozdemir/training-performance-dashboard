"""Turn warehouse activity rows into the daily metrics series (date spine, load, form, VDOT)."""

from collections import defaultdict
from datetime import date, datetime, timedelta

from config import AthleteParams
from metrics.intervals import session_vdot
from metrics.training_load import compute_daily_series
from metrics.trimp import banister_trimp
from metrics.vdot import vdot
from strava.transform import RACE_WORKOUT_TYPE

CATEGORIES = ("run", "crossfit", "other")


def activity_date(row: dict) -> date:
    return datetime.fromisoformat(row["start_date_local"]).date()


def activity_trimp(row: dict, athlete: AthleteParams) -> float | None:
    """TRIMP for one activity, or None when it has no heart-rate data."""
    if not row.get("average_heartrate") or not row.get("moving_time_s"):
        return None
    return banister_trimp(
        duration_min=row["moving_time_s"] / 60,
        avg_hr=row["average_heartrate"],
        resting_hr=athlete.resting_hr,
        max_hr=athlete.max_hr,
        sex=athlete.sex,
    )


def activity_vdot(row: dict) -> tuple[float, str] | None:
    """(VDOT, source) for a race or a lapped interval session, else None."""
    if row["category"] != "run":
        return None
    if row.get("workout_type") == RACE_WORKOUT_TYPE and row.get("distance_m"):
        return vdot(row["distance_m"], row["elapsed_time_s"]), "race"
    if row.get("laps"):
        estimate = session_vdot(row["laps"])
        if estimate is not None:
            return estimate, "interval"
    return None


def build_daily_metrics(rows: list[dict], athlete: AthleteParams, today: date) -> list[dict]:
    """One row per calendar day from the first activity to `today`, rest days included.

    Days without heart-rate data contribute zero load, so CTL/ATL are understated for
    periods where no watch HR was recorded.
    """
    if not rows:
        return []

    trimp_by_day: dict[date, dict[str, float]] = defaultdict(lambda: dict.fromkeys(CATEGORIES, 0.0))
    vdot_by_day: dict[date, tuple[float, str]] = {}

    for row in rows:
        day = activity_date(row)
        trimp = activity_trimp(row, athlete)
        if trimp is not None:
            trimp_by_day[day][row["category"]] += trimp

        estimate = activity_vdot(row)
        if estimate is not None:
            current = vdot_by_day.get(day)
            # A race is a stronger signal than an interval estimate on the same day.
            if current is None or (estimate[1] == "race" and current[1] != "race"):
                vdot_by_day[day] = estimate

    first_day = min(activity_date(row) for row in rows)
    days = [first_day + timedelta(days=i) for i in range((today - first_day).days + 1)]
    totals = [sum(trimp_by_day[d].values()) if d in trimp_by_day else 0.0 for d in days]
    load = compute_daily_series(totals)

    result = []
    for day, total, pmc in zip(days, totals, load, strict=True):
        per_category = trimp_by_day.get(day, dict.fromkeys(CATEGORIES, 0.0))
        vdot_value, vdot_source = vdot_by_day.get(day, (None, None))
        result.append(
            {
                "date": day.isoformat(),
                "daily_trimp": total,
                "trimp_run": per_category["run"],
                "trimp_crossfit": per_category["crossfit"],
                "trimp_other": per_category["other"],
                "ctl": pmc["ctl"],
                "atl": pmc["atl"],
                "tsb": pmc["tsb"],
                "vdot": vdot_value,
                "vdot_source": vdot_source,
            }
        )
    return result
