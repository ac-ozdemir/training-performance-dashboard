import pytest

from config import AthleteParams
from metrics.intervals import is_auto_lapped, select_work_laps, session_vdot
from metrics.vdot import vdot_from_interval_speed

ATHLETE = AthleteParams(resting_hr=48, max_hr=185, lthr=165, sex="male")
EASY, REP, JOG = 2.78, 4.17, 2.5  # m/s: 6:00/km warm-up, 4:00/km rep, 6:40/km recovery
HARD_HR, EASY_HR = 158.0, 138.0  # 90% of LTHR 165 is 148.5


def _lap(speed: float, seconds: int, hr: float = HARD_HR) -> dict:
    return {
        "average_speed": speed,
        "moving_time_s": seconds,
        "distance_m": round(speed * seconds),
        "average_heartrate": hr,
    }


def _session(reps: int, warmup: bool = True, rep_hr: float = HARD_HR) -> list[dict]:
    laps = [_lap(EASY, 337, 124), _lap(EASY, 300, 130)] if warmup else []
    for i in range(reps):
        laps.append(_lap(REP, 180, rep_hr))
        if i < reps - 1:
            laps.append(_lap(JOG, 90, 145))
    if warmup:
        laps.append(_lap(EASY, 271, 140))
    return laps


def _auto_lapped_run() -> list[dict]:
    # 1 km auto-laps with surges hidden inside some kilometres
    paces_s = [352, 291, 268, 299, 239, 305, 301]
    return [{"average_speed": 1000 / s, "moving_time_s": s, "distance_m": 1000.0} for s in paces_s]


def test_picks_reps_out_of_warmup_recovery_and_cooldown():
    work = select_work_laps(_session(reps=5))
    assert len(work) == 5
    assert all(lap["average_speed"] == REP for lap in work)


def test_works_when_reps_are_the_majority_of_laps():
    # 8 reps + 7 recoveries, no warm-up laps: a median-based threshold would fail here
    assert len(select_work_laps(_session(reps=8, warmup=False))) == 8


def test_auto_lapped_runs_are_not_interval_sessions():
    laps = _auto_lapped_run()
    assert is_auto_lapped(laps)
    assert select_work_laps(laps) == []


def test_manual_laps_are_not_mistaken_for_auto_laps():
    assert not is_auto_lapped(_session(reps=5))


def test_evenly_paced_run_has_no_reps():
    assert select_work_laps([_lap(3.5, 300), _lap(3.55, 300), _lap(3.48, 300)]) == []


def test_short_reps_are_excluded():
    laps = [_lap(EASY, 360), _lap(5.0, 80), _lap(JOG, 90), _lap(5.0, 80), _lap(EASY, 360)]
    assert select_work_laps(laps) == []


def test_single_fast_lap_is_not_a_session():
    assert select_work_laps([_lap(EASY, 337), _lap(REP, 240), _lap(EASY, 300)]) == []


def test_session_vdot_matches_rep_pace():
    assert session_vdot(_session(reps=5), ATHLETE) == pytest.approx(vdot_from_interval_speed(REP))
    # 4:00/km reps ~ VDOT 47.4 under the "I pace = vVO2max" assumption
    assert vdot_from_interval_speed(REP) == pytest.approx(47.4, abs=0.2)


def test_reps_below_effort_threshold_give_no_vdot():
    assert session_vdot(_session(reps=5, rep_hr=EASY_HR), ATHLETE) is None


def test_reps_without_heart_rate_give_no_vdot():
    laps = _session(reps=5)
    for lap in laps:
        lap["average_heartrate"] = None
    assert session_vdot(laps, ATHLETE) is None


def test_empty_laps():
    assert select_work_laps([]) == []
    assert session_vdot([], ATHLETE) is None
