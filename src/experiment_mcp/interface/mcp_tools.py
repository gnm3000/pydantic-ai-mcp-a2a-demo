"""FastMCP tools translating protocol inputs into application calls."""

import asyncio
from random import randint
from typing import Literal

from fastmcp import Context, FastMCP
from fastmcp.apps import AppConfig
from fastmcp.dependencies import Progress
from mcp.types import ElicitRequest, ElicitRequestFormParams, InputRequiredResult

from experiment_mcp.application.get_price_history import GetPriceHistory
from experiment_mcp.application.get_ticker_info import GetTickerInfo
from experiment_mcp.core.models import PriceHistory
from experiment_mcp.core.analysis import (
    compare_windows,
    summarize_prices as summarize_price_values,
    weighted_window_trend as calculate_weighted_window_trend,
)

MARKET_APP_URI = "ui://quantinsider/price-chart.html"
PRICE_PERIODS = ("5d", "1mo", "3mo", "6mo", "1y")


def register_tools(
    mcp: FastMCP,
    get_price_history_use_case: GetPriceHistory,
    get_ticker_info_use_case: GetTickerInfo | None = None,
) -> None:
    @mcp.tool
    def compare_price_windows(left: list[float], right: list[float]) -> dict[str, float | int | str]:
        """Compare two window averages and return the direction of change."""
        return compare_windows(left, right)

    @mcp.tool
    def weighted_window_trend(prices: list[float]) -> dict[str, int | str]:
        """Apply the wwindow_trend indicator to a price series."""
        return calculate_weighted_window_trend(prices)

    @mcp.tool
    def summarize_prices(prices: list[float]) -> dict[str, float | int]:
        """Summarize a series with its count, minimum, maximum, and average."""
        return summarize_price_values(prices)

    @mcp.tool
    def get_price_history(
        ticker: str,
        period: str = "1mo",
        interval: str = "1d",
        start: str | None = None,
        end: str | None = None,
    ) -> dict[str, object]:
        """Get historical OHLCV prices for a ticker, using cached data when available.

        Use this tool when a question requires prices, performance, or trends
        over a specific period. Choose `period` for a relative window such as
        `5d` or `1mo`; use `start` and `end` for specific dates. `interval` sets
        the granularity, for example `1d` for daily closes. The response
        contains available bars and does not include forecasts.
        """
        history = get_price_history_use_case.execute(
            ticker, period=period, interval=interval, start=start, end=end
        )
        return _serialize_history(history)

    @mcp.tool(
        app=AppConfig(resource_uri=MARKET_APP_URI),
        tags={"market-data", "visualization"},
    )
    def open_price_chart(
        ticker: str = "AAPL", period: str = "1mo", interval: str = "1d"
    ) -> dict[str, object]:
        """Open the interactive price chart for a ticker and time range."""
        history = get_price_history_use_case.execute(
            ticker, period=period, interval=interval
        )
        return _serialize_history(history)

    if get_ticker_info_use_case is not None:
        @mcp.tool(
            task=True,
            tags={"market-data", "long-running"},
            meta={
                "max_tickers": 5,
                "simulated_delay_seconds": "random 5-10",
                "elicitation": "choose_period_when_missing",
            },
        )
        async def analyze_multiple_tickers(
            ctx: Context,
            tickers: list[str],
            period: Literal["5d", "1mo", "3mo", "6mo", "1y"] | None = None,
            progress: Progress = Progress(),
        ) -> dict[str, object] | InputRequiredResult:
            """Build a price and company report for one to five tickers.

            If period is omitted, asks the user to choose it using MCP elicitation.
            A random 5–10 second pause per ticker simulates slow processing.
            Progress advances through the simulation and market-data fetch for
            every ticker.
            """
            if not 1 <= len(tickers) <= 5:
                raise ValueError("Provide between one and five tickers.")

            normalized = [ticker.strip().upper() for ticker in tickers]
            if any(not ticker for ticker in normalized):
                raise ValueError("Tickers cannot be empty.")

            responses = ctx.input_responses
            if period is None and responses is None:
                request = ElicitRequest(
                    method="elicitation/create",
                    params=ElicitRequestFormParams(
                        message="Which period should be analyzed for these tickers?",
                        requested_schema={
                            "type": "object",
                            "properties": {
                                "period": {
                                    "type": "string",
                                    "enum": list(PRICE_PERIODS),
                                    "title": "Period",
                                }
                            },
                            "required": ["period"],
                        },
                    ),
                )
                return InputRequiredResult(
                    result_type="input_required",
                    input_requests={"analysis_period": request},
                )

            if period is None:
                answer = responses.get("analysis_period") if responses else None
                if answer is None or answer.action != "accept" or answer.content is None:
                    return {"status": "cancelled", "results": []}
                period = answer.content.get("period")

            if period not in PRICE_PERIODS:
                raise ValueError(f"Invalid period. Choose one of: {', '.join(PRICE_PERIODS)}.")

            await progress.set_total(len(normalized) * 2)
            report = []
            for ticker in normalized:
                await progress.set_message(f"Simulating analysis for {ticker}")
                await asyncio.sleep(randint(5, 10))
                await progress.increment()
                await progress.set_message(f"Fetching profile and prices for {ticker}")
                info, history = await asyncio.gather(
                    asyncio.to_thread(get_ticker_info_use_case.execute, ticker),
                    asyncio.to_thread(
                        get_price_history_use_case.execute,
                        ticker,
                        period=period,
                        interval="1d",
                    ),
                )
                result = _serialize_history(history)
                result.update(
                    {"name": info.name, "sector": info.sector, "industry": info.industry}
                )
                report.append(result)
                await progress.increment()
            return {"status": "completed", "period": period, "results": report}


def _serialize_history(history: PriceHistory) -> dict[str, object]:
    prices = [{"date": bar.timestamp, **bar.values} for bar in history.bars]
    return {"ticker": history.ticker, "count": len(prices), "prices": prices}
