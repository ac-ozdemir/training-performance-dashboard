import pytest

from metrics.trimp import banister_trimp


def test_known_value_male():
    # 40min @ avgHR150, restHR50, maxHR190 — golden value from the formula
    # computed independently (see pipeline dev notes), not from the module under test.
    trimp = banister_trimp(duration_min=40, avg_hr=150, resting_hr=50, max_hr=190, sex="male")
    assert trimp == pytest.approx(72.0636, rel=1e-4)


def test_known_value_female():
    trimp = banister_trimp(duration_min=40, avg_hr=150, resting_hr=50, max_hr=190, sex="female")
    assert trimp == pytest.approx(80.9994, rel=1e-4)


def test_zero_when_avg_hr_equals_resting_hr():
    trimp = banister_trimp(duration_min=60, avg_hr=50, resting_hr=50, max_hr=190)
    assert trimp == 0.0


def test_clamped_to_zero_when_avg_hr_below_resting_hr():
    # shouldn't happen with real data, but must not raise or go negative
    trimp = banister_trimp(duration_min=60, avg_hr=40, resting_hr=50, max_hr=190)
    assert trimp == 0.0


def test_monotonic_in_avg_hr():
    low = banister_trimp(duration_min=30, avg_hr=120, resting_hr=50, max_hr=190)
    high = banister_trimp(duration_min=30, avg_hr=160, resting_hr=50, max_hr=190)
    assert high > low


def test_monotonic_in_duration():
    short = banister_trimp(duration_min=20, avg_hr=140, resting_hr=50, max_hr=190)
    long_ = banister_trimp(duration_min=60, avg_hr=140, resting_hr=50, max_hr=190)
    assert long_ > short


def test_zero_duration_is_zero():
    assert banister_trimp(duration_min=0, avg_hr=150, resting_hr=50, max_hr=190) == 0.0


@pytest.mark.parametrize(
    "bad_kwargs",
    [
        {"duration_min": -1, "avg_hr": 150, "resting_hr": 50, "max_hr": 190},
        {"duration_min": 40, "avg_hr": 150, "resting_hr": 190, "max_hr": 190},
        {"duration_min": 40, "avg_hr": 150, "resting_hr": 200, "max_hr": 190},
    ],
)
def test_invalid_inputs_raise(bad_kwargs):
    with pytest.raises(ValueError):
        banister_trimp(**bad_kwargs)


def test_invalid_sex_raises():
    with pytest.raises(ValueError):
        banister_trimp(duration_min=40, avg_hr=150, resting_hr=50, max_hr=190, sex="other")
