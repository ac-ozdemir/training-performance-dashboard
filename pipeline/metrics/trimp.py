"""Banister TRIMP (Training Impulse) calculation."""
import math

_MALE_K, _MALE_B = 0.64, 1.92
_FEMALE_K, _FEMALE_B = 0.86, 1.67


def banister_trimp(
    duration_min: float,
    avg_hr: float,
    resting_hr: float,
    max_hr: float,
    sex: str = "male",
) -> float:
    """Banister's exponential TRIMP for a single session.

    duration_min: session duration in minutes
    avg_hr, resting_hr, max_hr: heart rates in bpm
    sex: "male" or "female" — determines the weighting exponent (Banister's
    original coefficients were fit separately for men and women)
    """
    if duration_min < 0:
        raise ValueError("duration_min must be non-negative")
    if max_hr <= resting_hr:
        raise ValueError("max_hr must be greater than resting_hr")

    if sex == "male":
        k, b = _MALE_K, _MALE_B
    elif sex == "female":
        k, b = _FEMALE_K, _FEMALE_B
    else:
        raise ValueError(f"sex must be 'male' or 'female', got {sex!r}")

    hr_ratio = (avg_hr - resting_hr) / (max_hr - resting_hr)
    hr_ratio = max(hr_ratio, 0.0)

    return duration_min * hr_ratio * k * math.exp(b * hr_ratio)
