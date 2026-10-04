"""Separate work reps from warm-up/recovery/cool-down laps in a manually lapped interval run."""

from statistics import median

from config import AthleteParams
from metrics.vdot import vdot_from_interval_speed

MIN_REP_SECONDS = 150
MAX_REP_SECONDS = 360
MIN_SPEED_GAP_RATIO = 1.10
MIN_REPS = 2

AUTO_LAP_DISTANCES_M = (1000.0, 1609.34)
AUTO_LAP_TOLERANCE = 0.02
AUTO_LAP_SHARE = 0.6

# Reps averaging below this share of LTHR weren't run at VO2max effort; their pace would
# understate VDOT. A 3-minute rep's average lags its peak, hence 90% rather than 100%.
MIN_REP_HR_SHARE_OF_LTHR = 0.90


def is_auto_lapped(laps: list[dict]) -> bool:
    """True when most laps are the watch's automatic 1 km / 1 mile splits, not manual reps."""
    distances = [lap["distance_m"] for lap in laps if lap.get("distance_m")]
    if not distances:
        return False
    auto = sum(
        1
        for d in distances
        if any(abs(d - target) <= target * AUTO_LAP_TOLERANCE for target in AUTO_LAP_DISTANCES_M)
    )
    return auto / len(distances) >= AUTO_LAP_SHARE


def select_work_laps(laps: list[dict]) -> list[dict]:
    """Return the repetition laps of a manually lapped interval session.

    Laps are split into a fast and a slow group at the largest relative speed gap; the fast
    group is the work. This holds whether reps are the majority of laps or not. Only reps
    lasting 2.5-6 minutes are kept: Daniels' interval pace (~vVO2max) is defined for that
    range, and short reps (200-400 m) would overstate VDOT.
    """
    if is_auto_lapped(laps):
        return []

    speeds = sorted(lap["average_speed"] for lap in laps if lap.get("average_speed"))
    if len(speeds) < 2:
        return []

    gap_ratio, threshold = max(
        (upper / lower, upper) for lower, upper in zip(speeds, speeds[1:], strict=False)
    )
    if gap_ratio < MIN_SPEED_GAP_RATIO:
        return []

    reps = [
        lap
        for lap in laps
        if (lap.get("average_speed") or 0) >= threshold
        and MIN_REP_SECONDS <= (lap.get("moving_time_s") or 0) <= MAX_REP_SECONDS
    ]
    return reps if len(reps) >= MIN_REPS else []


def session_vdot(laps: list[dict], athlete: AthleteParams) -> float | None:
    """Median VDOT across reps run at VO2max effort, or None if fewer than two qualify."""
    min_hr = athlete.lthr * MIN_REP_HR_SHARE_OF_LTHR
    reps = [lap for lap in select_work_laps(laps) if (lap.get("average_heartrate") or 0) >= min_hr]
    if len(reps) < MIN_REPS:
        return None
    return median(vdot_from_interval_speed(lap["average_speed"]) for lap in reps)
