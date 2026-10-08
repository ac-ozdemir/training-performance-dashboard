"""VDOT from structured runs tagged "Workout" in Strava: interval reps or a tempo block.

Both read the fast laps of a manually lapped session. Laps are split into a fast and a
slow group at the largest relative speed gap, which separates work from warm-up,
recovery and cool-down whether the work is the majority of laps or not.
"""

from statistics import median

from config import AthleteParams
from metrics.vdot import vdot_from_interval_speed, vdot_from_threshold_speed

MIN_SPEED_GAP_RATIO = 1.10

# Interval reps: Daniels' interval (I) pace ~ vVO2max is defined for 3-5 minute reps.
MIN_REP_SECONDS = 150
MAX_REP_SECONDS = 360
MIN_REPS = 2
# A 3-minute rep's average lags its peak, hence 90% rather than 100% of LTHR.
MIN_REP_HR_SHARE_OF_LTHR = 0.90

# Tempo: Daniels' threshold (T) pace is the pace you could race for about an hour,
# typically run as one 20-40 minute block or as 2-3 cruise blocks of 10+ minutes.
MIN_TEMPO_BLOCK_SECONDS = 600
MAX_TEMPO_BLOCK_SECONDS = 2400
MIN_TEMPO_TOTAL_SECONDS = 900
MIN_TEMPO_HR_SHARE_OF_LTHR = 0.95

AUTO_LAP_DISTANCES_M = (1000.0, 1609.34)
AUTO_LAP_TOLERANCE = 0.02
AUTO_LAP_SHARE = 0.6


def is_auto_lapped(laps: list[dict]) -> bool:
    """True when most laps are the watch's automatic 1 km / 1 mile splits, not manual laps."""
    distances = [lap["distance_m"] for lap in laps if lap.get("distance_m")]
    if not distances:
        return False
    auto = sum(
        1
        for d in distances
        if any(abs(d - target) <= target * AUTO_LAP_TOLERANCE for target in AUTO_LAP_DISTANCES_M)
    )
    return auto / len(distances) >= AUTO_LAP_SHARE


def fast_laps(laps: list[dict]) -> list[dict]:
    """Laps above the largest relative speed gap, or [] when pacing is too even to split."""
    speeds = sorted(lap["average_speed"] for lap in laps if lap.get("average_speed"))
    if len(speeds) < 2:
        return []
    gap_ratio, threshold = max(
        (upper / lower, upper) for lower, upper in zip(speeds, speeds[1:], strict=False)
    )
    if gap_ratio < MIN_SPEED_GAP_RATIO:
        return []
    return [lap for lap in laps if (lap.get("average_speed") or 0) >= threshold]


def select_work_laps(laps: list[dict]) -> list[dict]:
    """Interval reps: fast laps of 2.5-6 minutes, at least two of them.

    Sessions recorded on automatic 1 km splits are skipped: a rep can't be told apart from
    the kilometre it happens to fall in.
    """
    if is_auto_lapped(laps):
        return []
    reps = [
        lap
        for lap in fast_laps(laps)
        if MIN_REP_SECONDS <= (lap.get("moving_time_s") or 0) <= MAX_REP_SECONDS
    ]
    return reps if len(reps) >= MIN_REPS else []


def select_tempo_blocks(laps: list[dict]) -> list[dict]:
    """Tempo blocks: fast laps of 10-40 minutes adding up to at least 15 minutes.

    Automatic 1 km splits never last 10 minutes at tempo pace, so warm-up kilometres on
    auto-lap don't disqualify the session; the block itself must be manually lapped.
    """
    blocks = [
        lap
        for lap in fast_laps(laps)
        if MIN_TEMPO_BLOCK_SECONDS <= (lap.get("moving_time_s") or 0) <= MAX_TEMPO_BLOCK_SECONDS
    ]
    total = sum(lap["moving_time_s"] for lap in blocks)
    return blocks if total >= MIN_TEMPO_TOTAL_SECONDS else []


def interval_vdot(laps: list[dict], athlete: AthleteParams) -> float | None:
    """Median VDOT across reps run at VO2max effort, or None if fewer than two qualify."""
    min_hr = athlete.lthr * MIN_REP_HR_SHARE_OF_LTHR
    reps = [lap for lap in select_work_laps(laps) if (lap.get("average_heartrate") or 0) >= min_hr]
    if len(reps) < MIN_REPS:
        return None
    return median(vdot_from_interval_speed(lap["average_speed"]) for lap in reps)


def tempo_vdot(laps: list[dict], athlete: AthleteParams) -> float | None:
    """VDOT from the time-weighted tempo pace, if the block was run at threshold effort."""
    blocks = select_tempo_blocks(laps)
    if not blocks or any(not lap.get("average_heartrate") for lap in blocks):
        return None
    seconds = sum(lap["moving_time_s"] for lap in blocks)
    avg_hr = sum(lap["average_heartrate"] * lap["moving_time_s"] for lap in blocks) / seconds
    if avg_hr < athlete.lthr * MIN_TEMPO_HR_SHARE_OF_LTHR:
        return None
    speed = sum(lap["distance_m"] for lap in blocks) / seconds
    return vdot_from_threshold_speed(speed)


def workout_vdot(laps: list[dict], athlete: AthleteParams) -> tuple[float, str] | None:
    """(VDOT, "interval" | "tempo") for a Workout-tagged run, or None if neither qualifies."""
    value = interval_vdot(laps, athlete)
    if value is not None:
        return value, "interval"
    value = tempo_vdot(laps, athlete)
    if value is not None:
        return value, "tempo"
    return None
