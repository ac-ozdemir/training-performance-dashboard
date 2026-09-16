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

    TSB follows the TrainingPeaks convention — it reflects the fitness/fatigue
    balance a day *starts* with, so it's computed from the previous day's CTL/ATL,
    before that day's own load is absorbed into the chronic/acute averages.
    """
    ctl, atl = initial_ctl, initial_atl
    rows = []
    for load in daily_loads:
        tsb = ctl - atl
        ctl = next_ctl(ctl, load)
        atl = next_atl(atl, load)
        rows.append({"load": load, "ctl": ctl, "atl": atl, "tsb": tsb})
    return rows
