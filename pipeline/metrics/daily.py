"""Turn warehouse activity rows into the daily metrics series (date spine, load, form, VDOT)."""

from collections import defaultdict
from datetime import date, datetime, timedelta
from statistics import mean

from config import AthleteParams
from metrics.intervals import session_vdot
from metrics.training_load import (
    ATL_TIME_CONSTANT_DAYS,
    CTL_TIME_CONSTANT_DAYS,
    compute_daily_series,
)
from metrics.trimp import banister_trimp
from metrics.vdot import vdot
from strava.transform import RACE_WORKOUT_TYPE

CATEGORIES = ("run", "crossfit", "other")


def activity_date(row: dict) -> date:
    return datetime.fromisoformat(row["start_date_local"]).date()


def activity_trimp(row: dict, athlete: AthleteParams) -> float | None:
    """TRIMP for one activity, or None when it has no heart-rate data (counted as zero load)."""
    if not row.get("average_heartrate") or not row.get("moving_time_s"):
        return None
    return banister_trimp(
        duration_min=row["moving_time_s"] / 60,
        avg_hr=row["average_heartrate"],
        resting_hr=athlete.resting_hr,
        max_hr=athlete.max_hr,
        sex=athlete.sex,
    )


def activity_vdot(row: dict, athlete: AthleteParams) -> tuple[float, str] | None:
    """(VDOT, source) for a race or a qualifying interval session, else None.

    "Race" is the athlete's own Strava tag, used only for races actually run all-out
    (a race paced for a friend stays a normal run).
    """
    if row["category"] != "run":
        return None
    if row.get("workout_type") == RACE_WORKOUT_TYPE and row.get("distance_m"):
        return vdot(row["distance_m"], row["elapsed_time_s"]), "race"
    if row.get("laps"):
        estimate = session_vdot(row["laps"], athlete)
        if estimate is not None:
            return estimate, "interval"
    return None


def _load_series(totals: list[float]) -> list[dict]:
    """CTL/ATL/TSB seeded with the opening period's mean load instead of zero.

    Starting from zero makes the first six weeks look like an artificial build-up.
    """
    initial_ctl = mean(totals[:CTL_TIME_CONSTANT_DAYS])
    initial_atl = mean(totals[:ATL_TIME_CONSTANT_DAYS])
    return compute_daily_series(totals, initial_ctl=initial_ctl, initial_atl=initial_atl)


def build_daily_metrics(
    rows: list[dict], athlete: AthleteParams, today: date, load_start: date
) -> list[dict]:
    """One row per calendar day from the first activity to `today`, rest days included.

    CTL/ATL/TSB are only computed from `load_start` (when heart-rate data becomes
    consistent); earlier days carry TRIMP and VDOT but no load values.
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

        estimate = activity_vdot(row, athlete)
        if estimate is not None:
            current = vdot_by_day.get(day)
            # A race is a stronger signal than an interval estimate on the same day.
            if current is None or (estimate[1] == "race" and current[1] != "race"):
                vdot_by_day[day] = estimate

    first_day = min(activity_date(row) for row in rows)
    days = [first_day + timedelta(days=i) for i in range((today - first_day).days + 1)]
    totals = [sum(trimp_by_day[d].values()) if d in trimp_by_day else 0.0 for d in days]

    load_days = [i for i, d in enumerate(days) if d >= load_start]
    load_by_index: dict[int, dict] = {}
    if load_days:
        series = _load_series([totals[i] for i in load_days])
        load_by_index = dict(zip(load_days, series, strict=True))

    result = []
    for i, (day, total) in enumerate(zip(days, totals, strict=True)):
        per_category = trimp_by_day.get(day, dict.fromkeys(CATEGORIES, 0.0))
        pmc = load_by_index.get(i, {})
        vdot_value, vdot_source = vdot_by_day.get(day, (None, None))
        result.append(
            {
                "date": day.isoformat(),
                "daily_trimp": total,
                "trimp_run": per_category["run"],
                "trimp_crossfit": per_category["crossfit"],
                "trimp_other": per_category["other"],
                "ctl": pmc.get("ctl"),
                "atl": pmc.get("atl"),
                "tsb": pmc.get("tsb"),
                "vdot": vdot_value,
                "vdot_source": vdot_source,
            }
        )
    return result
