import pytest

from metrics.intervals import select_work_laps, session_vdot
from metrics.vdot import vdot_from_interval_speed

EASY, REP, JOG = 2.78, 4.17, 2.5  # m/s: 6:00/km warm-up, 4:00/km rep, 6:40/km recovery


def _lap(speed: float, seconds: int) -> dict:
    return {"average_speed": speed, "moving_time_s": seconds}


def _session(reps: int, warmup: bool = True) -> list[dict]:
    laps = [_lap(EASY, 360), _lap(EASY, 360)] if warmup else []
    for i in range(reps):
        laps.append(_lap(REP, 240))
        if i < reps - 1:
            laps.append(_lap(JOG, 120))
    if warmup:
        laps.append(_lap(EASY, 400))
    return laps


def test_picks_reps_out_of_warmup_recovery_and_cooldown():
    work = select_work_laps(_session(reps=5))
    assert len(work) == 5
    assert all(lap["average_speed"] == REP for lap in work)


def test_works_when_reps_are_the_majority_of_laps():
    # 8 reps + 7 recoveries, no warm-up laps: a median-based threshold would fail here
    work = select_work_laps(_session(reps=8, warmup=False))
    assert len(work) == 8


def test_evenly_paced_run_has_no_reps():
    assert select_work_laps([_lap(3.5, 300), _lap(3.55, 300), _lap(3.48, 300)]) == []


def test_short_reps_are_excluded():
    laps = [_lap(EASY, 360), _lap(5.0, 80), _lap(JOG, 90), _lap(5.0, 80), _lap(EASY, 360)]
    assert select_work_laps(laps) == []


def test_too_few_laps():
    assert select_work_laps([_lap(REP, 240)]) == []
    assert session_vdot([]) is None


def test_session_vdot_matches_rep_pace():
    assert session_vdot(_session(reps=5)) == pytest.approx(vdot_from_interval_speed(REP))
    # 4:00/km reps ~ VDOT 47.4 under the "I pace = vVO2max" assumption
    assert vdot_from_interval_speed(REP) == pytest.approx(47.4, abs=0.2)
