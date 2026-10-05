"""Resource handler tests with deterministic market-data providers."""

import asyncio

from fastmcp import Client, FastMCP

from experiment_mcp.application.get_ticker_data import GetTickerData
from experiment_mcp.application.get_ticker_info import GetTickerInfo
from experiment_mcp.core.models import TickerInfo
from experiment_mcp.interface.mcp_resources import register_resources


class TickerInfoProvider:
    def get_ticker_info(self, ticker: str) -> TickerInfo:
        return TickerInfo(
            ticker, "Example Corp", "NASDAQ", "USD", "EQUITY", "Tech", "Software", "US", None, None
        )


class TickerDataProvider:
    def __init__(self) -> None:
        self.requests: list[tuple[str, str]] = []

    def get_ticker_data(self, ticker: str, kind: str) -> object:
        self.requests.append((ticker, kind))
        return {"kind": kind}


def test_all_ticker_resources_read_and_normalize_symbols():
    data_provider = TickerDataProvider()
    server = FastMCP("test")
    register_resources(
        server,
        GetTickerInfo(TickerInfoProvider()),
        GetTickerData(data_provider),
    )

    async def read_all():
        async with Client(server) as client:
            profile = await client.read_resource("market://symbols/aapl")
            resources = {
                kind: await client.read_resource(f"market://symbols/aapl/{kind}")
                for kind in ("quote", "recommendations", "calendar", "news", "actions")
            }
        return profile, resources

    profile, resources = asyncio.run(read_all())

    assert profile
    assert set(resources) == {"quote", "recommendations", "calendar", "news", "actions"}
    assert data_provider.requests == [
        ("AAPL", kind) for kind in ("quote", "recommendations", "calendar", "news", "actions")
    ]
