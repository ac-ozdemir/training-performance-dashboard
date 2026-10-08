"""Coggan-style Performance Management Chart (CTL/ATL/TSB), driven by daily TRIMP load."""

CTL_TIME_CONSTANT_DAYS = 42
ATL_TIME_CONSTANT_DAYS = 7


def next_ctl(prev_ctl: float, todays_load: float) -> float:
    """Chronic Training Load: 42-day exponentially weighted average of daily load."""
    return prev_ctl + (todays_load - prev_ctl) / CTL_TIME_CONSTANT_DAYS


def next_atl(prev_atl: float, todays_load: float) -> float:
    """Acute Training Load: 7-day exponentially weighted average of daily load."""
    return prev_atl + (todays_load - prev_atl) / ATL_TIME_CONSTANT_DAYS


def compute_daily_series(
    daily_loads: list[float],
    initial_ctl: float = 0.0,
    initial_atl: float = 0.0,
) -> list[dict]:
    """Roll a chronological list of daily TRIMP totals into CTL/ATL/TSB.

    daily_loads: one value per calendar day, oldest first, 0.0 for rest days.
    Returns one row per input day: {"load", "ctl", "atl", "tsb"}.

    TSB is the same day's CTL - ATL, so form always equals fitness minus fatigue as
    displayed. (TrainingPeaks instead uses the previous day's values — the balance a
    day starts with — which makes the three numbers shown for one day not add up.)
    """
    ctl, atl = initial_ctl, initial_atl
    rows = []
    for load in daily_loads:
        ctl = next_ctl(ctl, load)
        atl = next_atl(atl, load)
        rows.append({"load": load, "ctl": ctl, "atl": atl, "tsb": ctl - atl})
    return rows
