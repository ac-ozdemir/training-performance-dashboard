import pytest

from config import AthleteParams
from metrics.vdot import vdot_from_interval_speed, vdot_from_threshold_speed
from metrics.workouts import (
    interval_vdot,
    is_auto_lapped,
    select_tempo_blocks,
    select_work_laps,
    tempo_vdot,
    workout_vdot,
)

ATHLETE = AthleteParams(resting_hr=48, max_hr=185, lthr=165, sex="male")
EASY, REP, JOG = 2.78, 4.17, 2.5  # m/s: 6:00/km warm-up, 4:00/km rep, 6:40/km recovery
TEMPO = 1000 / 255  # 4:15/km
HARD_HR, EASY_HR = 158.0, 138.0  # 90% of LTHR 165 is 148.5
THRESHOLD_HR = 160.0  # 95% of LTHR 165 is 156.75


def _lap(speed: float, seconds: int, hr: float | None = HARD_HR) -> dict:
    return {
        "average_speed": speed,
        "moving_time_s": seconds,
        "distance_m": round(speed * seconds),
        "average_heartrate": hr,
    }


def _auto_km(speed: float, hr: float = 130.0) -> dict:
    return {
        "average_speed": speed,
        "moving_time_s": round(1000 / speed),
        "distance_m": 1000.0,
        "average_heartrate": hr,
    }


def _interval_session(reps: int, warmup: bool = True, rep_hr: float = HARD_HR) -> list[dict]:
    laps = [_lap(EASY, 337, 124), _lap(EASY, 300, 130)] if warmup else []
    for i in range(reps):
        laps.append(_lap(REP, 180, rep_hr))
        if i < reps - 1:
            laps.append(_lap(JOG, 90, 145))
    if warmup:
        laps.append(_lap(EASY, 271, 140))
    return laps


def _tempo_session(blocks: list[int], hr: float = THRESHOLD_HR) -> list[dict]:
    # Warm-up and cool-down on automatic 1 km splits, tempo blocks lapped by hand.
    laps = [_auto_km(EASY), _auto_km(EASY), _auto_km(EASY)]
    for i, seconds in enumerate(blocks):
        laps.append(_lap(TEMPO, seconds, hr))
        if i < len(blocks) - 1:
            laps.append(_lap(JOG, 120, 140))
    return laps + [_auto_km(EASY * 0.97), _auto_km(EASY * 0.97)]


# --- interval reps -------------------------------------------------------------------


def test_picks_reps_out_of_warmup_recovery_and_cooldown():
    work = select_work_laps(_interval_session(reps=5))
    assert len(work) == 5
    assert all(lap["average_speed"] == REP for lap in work)


def test_works_when_reps_are_the_majority_of_laps():
    # 8 reps + 7 recoveries, no warm-up laps: a median-based threshold would fail here
    assert len(select_work_laps(_interval_session(reps=8, warmup=False))) == 8


def test_auto_lapped_runs_have_no_reps():
    laps = [_auto_km(1000 / s) for s in (352, 291, 268, 299, 239, 305, 301)]
    assert is_auto_lapped(laps)
    assert select_work_laps(laps) == []


def test_manual_laps_are_not_mistaken_for_auto_laps():
    assert not is_auto_lapped(_interval_session(reps=5))


def test_evenly_paced_run_has_no_reps():
    assert select_work_laps([_lap(3.5, 300), _lap(3.55, 300), _lap(3.48, 300)]) == []


def test_short_reps_are_excluded():
    laps = [_lap(EASY, 360), _lap(5.0, 80), _lap(JOG, 90), _lap(5.0, 80), _lap(EASY, 360)]
    assert select_work_laps(laps) == []


def test_single_fast_lap_is_not_a_session():
    assert select_work_laps([_lap(EASY, 337), _lap(REP, 240), _lap(EASY, 300)]) == []


def test_interval_vdot_matches_rep_pace():
    laps = _interval_session(reps=5)
    assert interval_vdot(laps, ATHLETE) == pytest.approx(vdot_from_interval_speed(REP))
    # 4:00/km reps ~ VDOT 47.4 under the "I pace = vVO2max" assumption
    assert vdot_from_interval_speed(REP) == pytest.approx(47.4, abs=0.2)


def test_reps_below_effort_threshold_give_no_vdot():
    assert interval_vdot(_interval_session(reps=5, rep_hr=EASY_HR), ATHLETE) is None


def test_reps_without_heart_rate_give_no_vdot():
    laps = _interval_session(reps=5)
    for lap in laps:
        lap["average_heartrate"] = None
    assert interval_vdot(laps, ATHLETE) is None


# --- tempo blocks --------------------------------------------------------------------


def test_single_tempo_block_found_despite_auto_lapped_warmup():
    laps = _tempo_session([1500])
    assert is_auto_lapped(laps)  # warm-up and cool-down kilometres dominate the lap count
    blocks = select_tempo_blocks(laps)
    assert len(blocks) == 1
    assert blocks[0]["moving_time_s"] == 1500


def test_cruise_blocks_add_up():
    assert len(select_tempo_blocks(_tempo_session([720, 720]))) == 2


def test_too_little_tempo_time_is_not_a_tempo_run():
    assert select_tempo_blocks(_tempo_session([720])) == []


def test_tempo_vdot_scores_tempo_pace_as_one_hour_race_pace():
    laps = _tempo_session([1500])
    assert tempo_vdot(laps, ATHLETE) == pytest.approx(vdot_from_threshold_speed(TEMPO), rel=1e-3)
    # Daniels' tables put T pace at ~4:15/km for VDOT 50
    assert vdot_from_threshold_speed(TEMPO) == pytest.approx(49.6, abs=0.3)


def test_tempo_below_threshold_effort_gives_no_vdot():
    assert tempo_vdot(_tempo_session([1500], hr=150), ATHLETE) is None


def test_tempo_without_heart_rate_gives_no_vdot():
    assert tempo_vdot(_tempo_session([1500], hr=None), ATHLETE) is None


# --- classification ------------------------------------------------------------------


def test_workout_vdot_classifies_the_session():
    assert workout_vdot(_interval_session(reps=5), ATHLETE)[1] == "interval"
    assert workout_vdot(_tempo_session([1500]), ATHLETE)[1] == "tempo"
    assert workout_vdot([_lap(EASY, 2400, 135)], ATHLETE) is None


def test_empty_laps():
    assert select_work_laps([]) == []
    assert select_tempo_blocks([]) == []
    assert workout_vdot([], ATHLETE) is None
