import asyncio
import json
from pathlib import Path

import pytest
from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider

import experiment_mcp.infra.yfinance_ticker_info_provider as yfinance_info_module
from experiment_mcp.application.get_ticker_data import GetTickerData
from experiment_mcp.application.get_ticker_info import GetTickerInfo
from experiment_mcp.core.models import TickerInfo
from experiment_mcp.infra.yfinance_ticker_info_provider import (
    YFinanceTickerInfoProvider,
)
from experiment_mcp.interface.mcp_prompts import (
    build_analyze_ticker_prompt_v1,
    build_analyze_ticker_prompt_v2,
    register_prompts,
)
from experiment_mcp.interface.mcp_resources import register_resources


class FakeTickerInfoProvider:
    def __init__(self, result: TickerInfo) -> None:
        self.result = result
        self.requested_ticker = None

    def get_ticker_info(self, ticker: str) -> TickerInfo:
        self.requested_ticker = ticker
        return self.result


class FakeTickerDataProvider:
    def __init__(self) -> None:
        self.calls = []

    def get_ticker_data(self, ticker, kind):
        self.calls.append((ticker, kind))
        return {"sample": kind}


def test_use_case_normalizes_ticker_before_calling_provider():
    provider = FakeTickerInfoProvider(
        TickerInfo("AAPL", "Apple Inc.", None, None, None, None, None, None, None, None)
    )

    result = GetTickerInfo(provider).execute(" aapl ")

    assert provider.requested_ticker == "AAPL"
    assert result.ticker == "AAPL"


def test_use_case_rejects_blank_ticker():
    provider = FakeTickerInfoProvider(
        TickerInfo("", None, None, None, None, None, None, None, None, None)
    )

    with pytest.raises(ValueError, match="cannot be empty"):
        GetTickerInfo(provider).execute("  ")


def test_yfinance_adapter_maps_company_fields(monkeypatch):
    class FakeTicker:
        def __init__(self, ticker):
            self.ticker = ticker

        def get_info(self):
            return {
                "longName": "Apple Inc.",
                "exchange": "NMS",
                "currency": "USD",
                "quoteType": "EQUITY",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "country": "United States",
                "website": "https://www.apple.com",
                "longBusinessSummary": "Makes products.",
            }

    monkeypatch.setattr(yfinance_info_module.yf, "Ticker", FakeTicker)

    result = YFinanceTickerInfoProvider().get_ticker_info("AAPL")

    assert result == TickerInfo(
        ticker="AAPL",
        name="Apple Inc.",
        exchange="NMS",
        currency="USD",
        quote_type="EQUITY",
        sector="Technology",
        industry="Consumer Electronics",
        country="United States",
        website="https://www.apple.com",
        summary="Makes products.",
    )


def test_yfinance_adapter_falls_back_to_short_name_and_exchange_name(monkeypatch):
    class FakeTicker:
        def __init__(self, ticker):
            pass

        def get_info(self):
            return {"shortName": "Example Co.", "fullExchangeName": "Example Exchange"}

    monkeypatch.setattr(yfinance_info_module.yf, "Ticker", FakeTicker)

    result = YFinanceTickerInfoProvider().get_ticker_info("TEST")

    assert result.name == "Example Co."
    assert result.exchange == "Example Exchange"
    assert result.currency is None


def test_yfinance_adapter_rejects_unknown_ticker(monkeypatch):
    class FakeTicker:
        def __init__(self, ticker):
            pass

        def get_info(self):
            return {}

    monkeypatch.setattr(yfinance_info_module.yf, "Ticker", FakeTicker)

    with pytest.raises(ValueError, match="No information found"):
        YFinanceTickerInfoProvider().get_ticker_info("UNKNOWN")


def test_resource_template_reads_symbol_info_as_json():
    provider = FakeTickerInfoProvider(
        TickerInfo(
            "AAPL",
            "Apple Inc.",
            "NASDAQ",
            "USD",
            "EQUITY",
            "Technology",
            None,
            "United States",
            None,
            None,
        )
    )
    data_provider = FakeTickerDataProvider()
    app = FastMCP("test")
    register_resources(app, GetTickerInfo(provider), GetTickerData(data_provider))

    async def list_templates():
        return await app.list_resource_templates()

    templates = asyncio.run(list_templates())

    profile_template = next(
        item for item in templates if item.uri_template == "market://symbols/{ticker}"
    )
    assert profile_template.mime_type == "application/json"
    assert profile_template.tags == {"market-data", "ticker", "company-profile"}
    assert profile_template.meta == {"provider": "yfinance", "data_kind": "ticker-profile"}
    assert set(profile_template.parameters["properties"]) == {"ticker"}
    assert provider.requested_ticker is None


def test_extra_yfinance_resources_return_structured_data():
    info_provider = FakeTickerInfoProvider(
        TickerInfo("NVDA", "NVIDIA", None, None, None, None, None, None, None, None)
    )
    data_provider = FakeTickerDataProvider()
    app = FastMCP("test")
    register_resources(app, GetTickerInfo(info_provider), GetTickerData(data_provider))

    async def list_resources():
        return await app.list_resource_templates()

    templates = asyncio.run(list_resources())
    assert {item.uri_template for item in templates} >= {
        f"market://symbols/{{ticker}}/{kind}"
        for kind in ("quote", "recommendations", "calendar", "news", "actions")
    }
    for kind in ("quote", "recommendations", "calendar", "news", "actions"):
        assert GetTickerData(data_provider).execute(" nvda ", kind) == {"sample": kind}
    assert data_provider.calls == [
        ("NVDA", kind) for kind in ("quote", "recommendations", "calendar", "news", "actions")
    ]


def test_analyze_ticker_prompt_includes_profile_and_skill():
    app = FastMCP("test")
    app.add_provider(SkillsDirectoryProvider(roots=Path(__file__).resolve().parents[1] / "skills"))
    register_prompts(app)

    async def get_prompt():
        return await app.get_prompt("analyze_ticker")

    payload = json.loads(build_analyze_ticker_prompt_v2("nvda", "What is the recent price trend?"))
    assert asyncio.run(get_prompt()) is not None

    async def list_prompts():
        return await app.list_prompts()

    prompts = asyncio.run(list_prompts())
    assert {prompt.version for prompt in prompts if prompt.name == "analyze_ticker"} == {
        "1.0",
        "2.0",
    }
    assert payload["ticker"] == "NVDA"
    assert payload["question"] == "What is the recent price trend?"
    assert payload["context"]["company_profile"]["uri"] == "market://symbols/NVDA"
    assert payload["context"]["analysis_skill"]["uri"] == "skill://market-analysis/SKILL.md"


def test_analyze_ticker_prompt_v1_keeps_the_flat_contract():
    payload = json.loads(build_analyze_ticker_prompt_v1(" aapl "))

    assert payload["ticker"] == "AAPL"
    assert payload["profile_uri"] == "market://symbols/AAPL"
    assert payload["skill_uri"] == "skill://market-analysis/SKILL.md"


@pytest.mark.parametrize(
    "builder", [build_analyze_ticker_prompt_v1, build_analyze_ticker_prompt_v2]
)
def test_analyze_ticker_prompt_versions_reject_blank_tickers(builder):
    with pytest.raises(ValueError, match="cannot be empty"):
        builder("  ")
