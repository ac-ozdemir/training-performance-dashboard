"""Daniels & Gilbert VDOT estimation from a single race/time-trial effort."""
import math


def _vo2_from_velocity(velocity_m_per_min: float) -> float:
    return -4.60 + 0.182258 * velocity_m_per_min + 0.000104 * velocity_m_per_min**2


def _percent_vo2max_from_duration(duration_min: float) -> float:
    return (
        0.8
        + 0.1894393 * math.exp(-0.012778 * duration_min)
        + 0.2989558 * math.exp(-0.1932605 * duration_min)
    )


def vdot(distance_m: float, duration_s: float) -> float:
    """Estimate VDOT (Daniels & Gilbert) from a single maximal-effort run.

    distance_m: distance covered, in meters
    duration_s: time taken, in seconds

    Intended for race-pace or time-trial efforts, not easy/recovery runs —
    the formula assumes a near-maximal, evenly-paced effort.
    """
    if distance_m <= 0:
        raise ValueError("distance_m must be positive")
    if duration_s <= 0:
        raise ValueError("duration_s must be positive")

    duration_min = duration_s / 60
    velocity_m_per_min = distance_m / duration_min

    vo2 = _vo2_from_velocity(velocity_m_per_min)
    pct_vo2max = _percent_vo2max_from_duration(duration_min)

    return vo2 / pct_vo2max
