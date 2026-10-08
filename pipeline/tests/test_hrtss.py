import pytest

from metrics.hrtss import hr_tss


def test_one_hour_at_threshold_is_100():
    assert hr_tss(duration_min=60, avg_hr=165, lthr=165) == pytest.approx(100.0)


def test_scales_with_square_of_intensity():
    # 90% of LTHR for an hour -> 0.9^2 * 100
    assert hr_tss(duration_min=60, avg_hr=148.5, lthr=165) == pytest.approx(81.0)


def test_scales_linearly_with_duration():
    assert hr_tss(duration_min=120, avg_hr=165, lthr=165) == pytest.approx(200.0)


def test_zero_duration_is_zero():
    assert hr_tss(duration_min=0, avg_hr=150, lthr=165) == 0.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"duration_min": -1, "avg_hr": 150, "lthr": 165},
        {"duration_min": 60, "avg_hr": 150, "lthr": 0},
    ],
)
def test_invalid_inputs_raise(kwargs):
    with pytest.raises(ValueError):
        hr_tss(**kwargs)
