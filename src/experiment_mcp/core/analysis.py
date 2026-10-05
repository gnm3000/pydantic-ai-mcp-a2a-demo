"""Pure price-analysis rules adapted from Quantinsider's Template.py."""

from collections.abc import Sequence


def validate_prices(prices: Sequence[float], minimum: int = 1) -> list[float]:
    values = [float(price) for price in prices]
    if len(values) < minimum:
        raise ValueError(f"At least {minimum} prices are required.")
    return values


def average(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def window_trend(left: Sequence[float], right: Sequence[float]) -> int:
    """Return 1 when the right average rises, -1 when it falls, else 0."""
    left_average = average(left)
    right_average = average(right)
    return (right_average > left_average) - (right_average < left_average)


def compare_windows(left: Sequence[float], right: Sequence[float]) -> dict[str, float | int | str]:
    left_values = validate_prices(left)
    right_values = validate_prices(right)
    direction = window_trend(left_values, right_values)
    return {
        "left_average": average(left_values),
        "right_average": average(right_values),
        "direction": direction,
        "label": {1: "up", 0: "flat", -1: "down"}[direction],
    }


def weighted_window_trend(prices: Sequence[float]) -> dict[str, int | str]:
    """Calculate Quantinsider's wwindow_trend score for a price series."""
    values = validate_prices(prices, minimum=4)
    midpoint = len(values) // 2
    left, right = values[:midpoint], values[midpoint:]
    if len(left) < 2 or len(right) < 2:
        raise ValueError("At least 4 prices are required to calculate the trend.")

    left_midpoint = len(left) // 2
    right_midpoint = len(right) // 2
    score = (
        window_trend(left, right)
        + window_trend(left[:left_midpoint], left[left_midpoint:])
        + window_trend(right[:right_midpoint], right[right_midpoint:])
    )
    return {"score": score, "label": "up" if score > 0 else "down" if score < 0 else "flat"}


def summarize_prices(prices: Sequence[float]) -> dict[str, float | int]:
    values = validate_prices(prices)
    return {
        "count": len(values),
        "minimum": min(values),
        "maximum": max(values),
        "average": average(values),
    }
