import asyncio

from fastmcp import FastMCP

import experiment_mcp.server as server_module
from experiment_mcp.application.get_price_history import GetPriceHistory
from experiment_mcp.application.get_ticker_info import GetTickerInfo
from experiment_mcp.core.models import PriceBar, PriceHistory, TickerInfo
from experiment_mcp.interface.mcp_tools import register_tools
from experiment_mcp.server import mcp


class FakeProvider:
    def get_history(self, ticker, **kwargs):
        return PriceHistory(ticker, (PriceBar("2025-01-02T00:00:00+00:00", {"Close": 10.5}),))


class FakeCache:
    def get(self, key):
        return None

    def set(self, key, history):
        pass


class FakeTickerInfoProvider:
    def get_ticker_info(self, ticker):
        return TickerInfo(
            ticker, f"{ticker} Inc.", None, "USD", "EQUITY", "Technology",
            "Software", "US", None, None,
        )


def build_app():
    app = FastMCP("test")
    use_case = GetPriceHistory(FakeProvider(), FakeCache())
    register_tools(app, use_case, GetTickerInfo(FakeTickerInfoProvider()))
    return app


def test_server_registers_all_tools():
    tool_names = {tool.name for tool in asyncio.run(mcp.list_tools())}

    assert tool_names == {
        "compare_price_windows",
        "weighted_window_trend",
        "summarize_prices",
        "get_price_history",
        "open_price_chart",
        "analyze_multiple_tickers",
    }


def test_analysis_tools_call_core_functions():
    app = build_app()

    async def get_tools():
        return await asyncio.gather(
            app.get_tool("summarize_prices"),
            app.get_tool("compare_price_windows"),
            app.get_tool("weighted_window_trend"),
        )

    summary, compare, trend = asyncio.run(get_tools())

    assert summary.fn([2, 4, 6]) == {
        "count": 3,
        "minimum": 2.0,
        "maximum": 6.0,
        "average": 4.0,
    }
    assert compare.fn([1, 2], [3, 4])["label"] == "up"
    assert trend.fn([1, 2, 3, 4]) == {"score": 3, "label": "up"}


def test_price_history_tool_adapts_domain_model_to_dict():
    app = build_app()
    tool = asyncio.run(app.get_tool("get_price_history"))

    assert tool.fn("aapl") == {
        "ticker": "AAPL",
        "count": 1,
        "prices": [{"date": "2025-01-02T00:00:00+00:00", "Close": 10.5}],
    }


def test_open_price_chart_returns_app_data():
    app = build_app()
    tool = asyncio.run(app.get_tool("open_price_chart"))

    assert tool.fn("aapl") == {
        "ticker": "AAPL",
        "count": 1,
        "prices": [{"date": "2025-01-02T00:00:00+00:00", "Close": 10.5}],
    }
    assert tool.meta["ui"]["resourceUri"] == "ui://quantinsider/price-chart.html"


def test_server_main_runs_http_transport(monkeypatch):
    calls = {}
    monkeypatch.setattr(server_module.mcp, "run", lambda **kwargs: calls.update(kwargs))

    server_module.main()

    assert calls == {"transport": "http", "host": "0.0.0.0", "port": 8000}


def test_multi_ticker_task_reports_progress_and_company_data(monkeypatch):
    app = build_app()
    tool = asyncio.run(app.get_tool("analyze_multiple_tickers"))
    pauses = []

    async def fake_sleep(seconds):
        pauses.append(seconds)

    async def fake_to_thread(function, *args, **kwargs):
        return function(*args, **kwargs)

    class FakeProgress:
        def __init__(self):
            self.total = None
            self.messages = []
            self.steps = 0

        async def set_total(self, total):
            self.total = total

        async def set_message(self, message):
            self.messages.append(message)

        async def increment(self):
            self.steps += 1

    monkeypatch.setattr("experiment_mcp.interface.mcp_tools.asyncio.sleep", fake_sleep)
    monkeypatch.setattr("experiment_mcp.interface.mcp_tools.asyncio.to_thread", fake_to_thread)
    monkeypatch.setattr("experiment_mcp.interface.mcp_tools.randint", lambda low, high: low)
    progress = FakeProgress()

    class FakeContext:
        input_responses = None

    result = asyncio.run(tool.fn(FakeContext(), [" aapl ", "MSFT"], "1mo", progress))

    assert result["status"] == "completed"
    assert [company["ticker"] for company in result["results"]] == ["AAPL", "MSFT"]
    assert result["results"][0]["sector"] == "Technology"
    assert pauses == [5, 5]
    assert progress.total == progress.steps == 4
    assert progress.messages == [
        "Simulating analysis for AAPL",
        "Fetching profile and prices for AAPL",
        "Simulating analysis for MSFT",
        "Fetching profile and prices for MSFT",
    ]


def test_multi_ticker_task_rejects_more_than_five_tickers():
    app = build_app()
    tool = asyncio.run(app.get_tool("analyze_multiple_tickers"))

    try:
        asyncio.run(tool.fn(object(), ["A", "B", "C", "D", "E", "F"]))
    except ValueError as error:
        assert "one and five" in str(error)
    else:
        raise AssertionError("Expected more than five tickers to be rejected")


def test_multi_ticker_task_rejects_empty_ticker():
    app = build_app()
    tool = asyncio.run(app.get_tool("analyze_multiple_tickers"))

    try:
        asyncio.run(tool.fn(object(), [" "]))
    except ValueError as error:
        assert "cannot be empty" in str(error)
    else:
        raise AssertionError("Expected an empty ticker to be rejected")


def test_multi_ticker_task_requests_period_when_omitted():
    from mcp.types import InputRequiredResult

    app = build_app()
    tool = asyncio.run(app.get_tool("analyze_multiple_tickers"))

    class FakeContext:
        input_responses = None

    result = asyncio.run(tool.fn(FakeContext(), ["NVDA"]))

    assert isinstance(result, InputRequiredResult)
    request = result.input_requests["analysis_period"]
    assert request.params.requested_schema["properties"]["period"]["enum"] == [
        "5d", "1mo", "3mo", "6mo", "1y"
    ]


def test_multi_ticker_task_rejects_unsupported_period():
    app = build_app()
    tool = asyncio.run(app.get_tool("analyze_multiple_tickers"))

    class FakeContext:
        input_responses = None

    try:
        asyncio.run(tool.fn(FakeContext(), ["NVDA"], "2y"))
    except ValueError as error:
        assert "Invalid period" in str(error)
    else:
        raise AssertionError("Expected an invalid period to be rejected")
