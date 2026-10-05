"""Tests for the dedicated FastMCP CodeMode endpoint."""

import asyncio

import pytest
from fastmcp import Client

from experiment_mcp.application.get_price_history import GetPriceHistory
from experiment_mcp.code_mode_server import create_code_mode_server
from experiment_mcp.core.models import PriceBar, PriceHistory


class PriceProvider:
    def get_history(self, ticker, **_kwargs):
        return PriceHistory(
            ticker,
            tuple(
                PriceBar(f"2026-01-0{index}T00:00:00+00:00", {"Close": value})
                for index, value in enumerate((10.0, 12.0, 14.0, 16.0), start=1)
            ),
        )


class HistoryCache:
    def get(self, _key):
        return None

    def set(self, _key, _history):
        pass


def build_server(*, auth_required=False):
    history = GetPriceHistory(PriceProvider(), HistoryCache())
    return create_code_mode_server(auth_required=auth_required, get_price_history=history)


def test_server_exposes_only_code_mode_meta_tools():
    server = build_server()
    tools = asyncio.run(server.list_tools())

    assert {tool.name for tool in tools} == {"search", "get_schema", "execute"}


def test_code_execution_chains_price_history_and_summary_tools():
    server = build_server()
    code = """history = await call_tool(
    "get_price_history", {"ticker": "NVDA", "period": "1mo", "interval": "1d"}
)
closes = [bar["Close"] for bar in history["prices"]]
summary = await call_tool("summarize_prices", {"prices": closes})
comparison = await call_tool(
    "compare_price_windows", {"earlier_prices": closes[:2], "later_prices": closes[2:]}
)
trend = await call_tool("weighted_window_trend", {"prices": closes})
return {"ticker": history["ticker"], "summary": summary, "comparison": comparison, "trend": trend}
"""

    async def execute():
        async with Client(server) as client:
            return await client.call_tool("execute", {"code": code}, raise_on_error=False)

    result = asyncio.run(execute())
    response = "\n".join(item.text for item in result.content if item.type == "text")

    assert not result.is_error
    assert "NVDA" in response
    assert "average" in response
    assert "13.0" in response
    assert "up" in response


@pytest.mark.parametrize(
    "code",
    [
        "this is not valid Python (",
        'return await call_tool("not_a_market_tool", {})',
        'return await call_tool("summarize_prices", {"prices": []})',
    ],
)
def test_code_execution_reports_invalid_code_tools_and_inputs(code):
    server = build_server()

    async def execute():
        async with Client(server) as client:
            return await client.call_tool("execute", {"code": code}, raise_on_error=False)

    result = asyncio.run(execute())

    assert result.is_error


def test_code_execution_enforces_tool_call_limit():
    server = build_server()
    code = "\n".join(
        'await call_tool("summarize_prices", {"prices": [1, 2, 3, 4]})' for _ in range(9)
    )

    async def execute():
        async with Client(server) as client:
            return await client.call_tool("execute", {"code": code}, raise_on_error=False)

    result = asyncio.run(execute())

    assert result.is_error


def test_server_requires_local_auth_by_default(monkeypatch):
    monkeypatch.delenv("MCP_DEV_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="MCP_DEV_TOKEN"):
        build_server(auth_required=True)


def test_server_accepts_configured_local_auth_token(monkeypatch):
    monkeypatch.setenv("MCP_DEV_TOKEN", "local-test-token-0123456789abcdef")

    server = build_server(auth_required=True)

    assert server.name == "Market Data CodeMode Demo"


def test_server_builds_default_market_data_adapters():
    server = create_code_mode_server(auth_required=False)

    assert {tool.name for tool in asyncio.run(server.list_tools())} == {
        "search",
        "get_schema",
        "execute",
    }


def test_main_loads_environment_and_runs_the_http_server(monkeypatch):
    from experiment_mcp import bootstrap, code_mode_server

    calls = []

    class FakeServer:
        def run(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(bootstrap, "load_environment", lambda: calls.append("environment"))
    monkeypatch.setattr(code_mode_server, "create_code_mode_server", FakeServer)

    code_mode_server.main()

    assert calls == [
        "environment",
        {"transport": "http", "host": "0.0.0.0", "port": 8001},
    ]
