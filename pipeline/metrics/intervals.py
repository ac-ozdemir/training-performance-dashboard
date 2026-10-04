"""Separate work reps from warm-up/recovery/cool-down laps in a manually lapped interval run."""

from statistics import median

from metrics.vdot import vdot_from_interval_speed

MIN_REP_SECONDS = 150
MAX_REP_SECONDS = 360
MIN_SPEED_GAP_RATIO = 1.10


def select_work_laps(laps: list[dict]) -> list[dict]:
    """Return the repetition laps of an interval session.

    Laps are split into a fast and a slow group at the largest relative speed gap; the fast
    group is the work. This holds whether reps are the majority of laps or not. Only reps
    lasting 2.5-6 minutes are kept: Daniels' interval pace (~vVO2max) is defined for that
    range, and short reps (200-400 m) would overstate VDOT.
    """
    speeds = sorted(lap["average_speed"] for lap in laps if lap.get("average_speed"))
    if len(speeds) < 2:
        return []

    gap_ratio, threshold = max(
        (upper / lower, upper) for lower, upper in zip(speeds, speeds[1:], strict=False)
    )
    if gap_ratio < MIN_SPEED_GAP_RATIO:
        return []

    return [
        lap
        for lap in laps
        if (lap.get("average_speed") or 0) >= threshold
        and MIN_REP_SECONDS <= (lap.get("moving_time_s") or 0) <= MAX_REP_SECONDS
    ]


def session_vdot(laps: list[dict]) -> float | None:
    """Median VDOT across the session's work reps, or None if no qualifying reps."""
    reps = select_work_laps(laps)
    if not reps:
        return None
    return median(vdot_from_interval_speed(lap["average_speed"]) for lap in reps)
