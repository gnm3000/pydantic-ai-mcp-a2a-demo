"""Read-only market tools exposed through a FastMCP CodeMode transform."""

from fastmcp import FastMCP

from experiment_mcp.application.get_price_history import GetPriceHistory
from experiment_mcp.core.analysis import (
    compare_windows,
)
from experiment_mcp.core.analysis import (
    summarize_prices as summarize_price_values,
)
from experiment_mcp.core.analysis import (
    weighted_window_trend as calculate_weighted_window_trend,
)
from experiment_mcp.core.models import PriceHistory


def register_code_mode_tools(mcp: FastMCP, history_use_case: GetPriceHistory) -> None:
    """Register the small, read-only market catalog available to CodeMode."""

    @mcp.tool(tags={"market-data", "read-only"})
    def get_price_history(
        ticker: str,
        period: str = "1mo",
        interval: str = "1d",
        start: str | None = None,
        end: str | None = None,
    ) -> dict[str, object]:
        """Fetch historical OHLCV bars for a ticker from the market-data provider."""
        history = history_use_case.execute(
            ticker, period=period, interval=interval, start=start, end=end
        )
        return _serialize_history(history)

    @mcp.tool(tags={"market-data", "analysis", "read-only"})
    def summarize_prices(prices: list[float]) -> dict[str, float | int]:
        """Return the count, minimum, maximum, and average for closing prices."""
        return summarize_price_values(prices)

    @mcp.tool(tags={"market-data", "analysis", "read-only"})
    def compare_price_windows(
        earlier_prices: list[float], later_prices: list[float]
    ) -> dict[str, float | int | str]:
        """Compare average prices from two chronological windows."""
        return compare_windows(earlier_prices, later_prices)

    @mcp.tool(tags={"market-data", "analysis", "read-only"})
    def weighted_window_trend(prices: list[float]) -> dict[str, int | str]:
        """Calculate the weighted trend across the supplied closing-price series."""
        return calculate_weighted_window_trend(prices)


def _serialize_history(history: PriceHistory) -> dict[str, object]:
    prices = [{"date": bar.timestamp, **bar.values} for bar in history.bars]
    return {"ticker": history.ticker, "count": len(prices), "prices": prices}
