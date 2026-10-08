"""Heart-rate TSS (hrTSS), used as an independent cross-check for Banister TRIMP."""


def hr_tss(duration_min: float, avg_hr: float, lthr: float) -> float:
    """Average-heart-rate approximation of TrainingPeaks' hrTSS.

    An hour at lactate-threshold heart rate scores 100; the intensity factor is
    avg_hr / lthr and the score scales with its square. TrainingPeaks weights time in
    zones instead of using the session average, so this reads a little low for
    sessions with large swings (intervals, HIIT).
    """
    if duration_min < 0:
        raise ValueError("duration_min must be non-negative")
    if lthr <= 0:
        raise ValueError("lthr must be positive")
    intensity = max(avg_hr, 0) / lthr
    return duration_min / 60 * intensity**2 * 100
