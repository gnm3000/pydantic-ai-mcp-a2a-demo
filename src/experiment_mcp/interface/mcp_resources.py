"""FastMCP resource templates for read-only market context."""

import asyncio

from fastmcp import Context, FastMCP

from experiment_mcp.application.get_ticker_data import GetTickerData
from experiment_mcp.application.get_ticker_info import GetTickerInfo
from experiment_mcp.application.ports import TickerDataKind


def register_resources(
    mcp: FastMCP,
    get_ticker_info: GetTickerInfo,
    get_ticker_data: GetTickerData,
) -> None:
    @mcp.resource(
        uri="market://symbols/{ticker}",
        name="Ticker information",
        description=(
            "Read company profile and classification data for a market ticker, "
            "including its exchange, currency, sector, industry and business summary."
        ),
        mime_type="application/json",
        tags={"market-data", "ticker", "company-profile"},
        meta={"provider": "yfinance", "data_kind": "ticker-profile"},
    )
    async def read_ticker_info(ctx: Context, ticker: str) -> dict[str, str | None]:
        """Read name, exchange, currency, sector, industry and business summary."""
        info = await asyncio.to_thread(get_ticker_info.execute, ticker)
        accessed_at = ctx.request_id if ctx.request_context is not None else None
        return {
            "ticker": info.ticker,
            "name": info.name,
            "exchange": info.exchange,
            "currency": info.currency,
            "quote_type": info.quote_type,
            "sector": info.sector,
            "industry": info.industry,
            "country": info.country,
            "website": info.website,
            "summary": info.summary,
            "accessed_at": accessed_at,
        }

    @mcp.resource(
        uri="market://symbols/{ticker}/quote",
        name="Ticker quote snapshot",
        description="Read the latest quote and market statistics exposed by yfinance fast_info.",
        mime_type="application/json",
        tags={"market-data", "ticker", "quote"},
        meta={"provider": "yfinance", "data_kind": "quote"},
    )
    async def read_ticker_quote(ctx: Context, ticker: str) -> dict[str, object]:
        """Read current quote fields such as price, volume, range and market cap."""
        return await _read_ticker_data(ctx, ticker, "quote", get_ticker_data)

    @mcp.resource(
        uri="market://symbols/{ticker}/recommendations",
        name="Analyst recommendations",
        description="Read recent analyst recommendation counts by period from yfinance.",
        mime_type="application/json",
        tags={"market-data", "ticker", "analyst-data"},
        meta={"provider": "yfinance", "data_kind": "recommendations"},
    )
    async def read_recommendations(ctx: Context, ticker: str) -> dict[str, object]:
        """Read analyst recommendation counts for the ticker."""
        return await _read_ticker_data(ctx, ticker, "recommendations", get_ticker_data)

    @mcp.resource(
        uri="market://symbols/{ticker}/calendar",
        name="Ticker event calendar",
        description="Read upcoming company events such as earnings when available in yfinance.",
        mime_type="application/json",
        tags={"market-data", "ticker", "calendar"},
        meta={"provider": "yfinance", "data_kind": "calendar"},
    )
    async def read_ticker_calendar(ctx: Context, ticker: str) -> dict[str, object]:
        """Read upcoming earnings and company calendar events."""
        return await _read_ticker_data(ctx, ticker, "calendar", get_ticker_data)

    @mcp.resource(
        uri="market://symbols/{ticker}/news",
        name="Recent ticker news",
        description="Read up to five recent news headlines associated with the ticker.",
        mime_type="application/json",
        tags={"market-data", "ticker", "news"},
        meta={"provider": "yfinance", "data_kind": "news"},
    )
    async def read_ticker_news(ctx: Context, ticker: str) -> dict[str, object]:
        """Read recent ticker news headlines and their available metadata."""
        return await _read_ticker_data(ctx, ticker, "news", get_ticker_data)

    @mcp.resource(
        uri="market://symbols/{ticker}/actions",
        name="Ticker corporate actions",
        description="Read historical dividends and stock splits exposed by yfinance.",
        mime_type="application/json",
        tags={"market-data", "ticker", "corporate-actions"},
        meta={"provider": "yfinance", "data_kind": "actions"},
    )
    async def read_ticker_actions(ctx: Context, ticker: str) -> dict[str, object]:
        """Read the ticker's historical dividends and stock splits."""
        return await _read_ticker_data(ctx, ticker, "actions", get_ticker_data)


async def _read_ticker_data(
    ctx: Context,
    ticker: str,
    kind: TickerDataKind,
    use_case: GetTickerData,
) -> dict[str, object]:
    data = await asyncio.to_thread(use_case.execute, ticker, kind)
    accessed_at = ctx.request_id if ctx.request_context is not None else None
    return {"ticker": ticker.strip().upper(), "data": data, "accessed_at": accessed_at}
