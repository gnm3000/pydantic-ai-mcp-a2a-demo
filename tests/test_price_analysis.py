import pytest

from experiment_mcp.core.analysis import (
    compare_windows,
    summarize_prices,
    weighted_window_trend,
)


def test_compare_windows_reports_rising_average():
    assert compare_windows([1, 2], [3, 4]) == {
        "left_average": 1.5,
        "right_average": 3.5,
        "direction": 1,
        "label": "up",
    }


def test_compare_windows_reports_flat_average():
    result = compare_windows([1, 3], [2, 2])

    assert result["direction"] == 0
    assert result["label"] == "flat"


def test_weighted_window_trend_rejects_too_few_prices():
    with pytest.raises(ValueError, match="At least 4"):
        weighted_window_trend([1, 2, 3])


@pytest.mark.parametrize(
    ("prices", "expected"),
    [
        ([1, 2, 3, 4], {"score": 3, "label": "up"}),
        ([4, 3, 2, 1], {"score": -3, "label": "down"}),
        ([2, 2, 2, 2], {"score": 0, "label": "flat"}),
    ],
)
def test_weighted_window_trend_scores_both_halves(prices, expected):
    assert weighted_window_trend(prices) == expected


def test_summarize_prices_returns_basic_statistics():
    assert summarize_prices([3, 1, 2]) == {
        "count": 3,
        "minimum": 1.0,
        "maximum": 3.0,
        "average": 2.0,
    }


def test_summarize_prices_rejects_empty_input():
    with pytest.raises(ValueError, match="At least 1"):
        summarize_prices([])
