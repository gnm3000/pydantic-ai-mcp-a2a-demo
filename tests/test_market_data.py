from pathlib import Path

import pandas as pd
import pytest

import experiment_mcp.infra.yfinance_provider as yfinance_module
from experiment_mcp.application.get_price_history import GetPriceHistory
from experiment_mcp.core.models import PriceBar, PriceHistory
from experiment_mcp.infra.json_history_cache import JsonFileHistoryCache
from experiment_mcp.infra.yfinance_provider import YFinanceProvider


def sample_history(ticker: str = "AAPL") -> PriceHistory:
    return PriceHistory(
        ticker,
        (
            PriceBar("2025-01-02T00:00:00-05:00", {"Close": 10.5, "Volume": 100.0}),
            PriceBar("2025-01-03T00:00:00-05:00", {"Close": 11.0, "Volume": 200.0}),
        ),
    )


class FakeMarketDataProvider:
    def __init__(self, history: PriceHistory) -> None:
        self.history = history
        self.calls = []

    def get_history(self, ticker, **kwargs):
        self.calls.append((ticker, kwargs))
        return PriceHistory(ticker, self.history.bars)


def test_use_case_fetches_once_for_repeated_request(tmp_path: Path):
    source = FakeMarketDataProvider(sample_history())
    use_case = GetPriceHistory(source, JsonFileHistoryCache(tmp_path))

    first = use_case.execute("aapl", period="5d")
    second = use_case.execute("AAPL", period="5d")

    assert source.calls == [("AAPL", {"period": "5d", "interval": "1d", "start": None, "end": None})]
    assert first == second


def test_json_cache_persists_history_between_instances(tmp_path: Path):
    source = FakeMarketDataProvider(sample_history())
    first_use_case = GetPriceHistory(source, JsonFileHistoryCache(tmp_path))
    first = first_use_case.execute("MSFT", period="5d")

    second_source = FakeMarketDataProvider(sample_history("MSFT"))
    second_use_case = GetPriceHistory(second_source, JsonFileHistoryCache(tmp_path))
    second = second_use_case.execute("MSFT", period="5d")

    assert first == second
    assert second_source.calls == []
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_request_params_are_part_of_cache_key(tmp_path: Path):
    source = FakeMarketDataProvider(sample_history())
    use_case = GetPriceHistory(source, JsonFileHistoryCache(tmp_path))

    use_case.execute("MSFT", start="2025-01-01", end="2025-01-05", interval="1d")
    use_case.execute("MSFT", start="2025-01-01", end="2025-01-05", interval="1h")

    assert len(source.calls) == 2


def test_expired_cache_entry_is_fetched_again(tmp_path: Path, monkeypatch):
    import experiment_mcp.infra.json_history_cache as cache_module

    clock = [1000.0]
    monkeypatch.setattr(cache_module.time, "time", lambda: clock[0])
    source = FakeMarketDataProvider(sample_history())
    use_case = GetPriceHistory(source, JsonFileHistoryCache(tmp_path, ttl_seconds=60))

    use_case.execute("MSFT", period="5d")
    clock[0] += 61
    use_case.execute("MSFT", period="5d")

    assert len(source.calls) == 2


def test_date_range_requires_both_start_and_end(tmp_path: Path):
    use_case = GetPriceHistory(FakeMarketDataProvider(sample_history()), JsonFileHistoryCache(tmp_path))

    with pytest.raises(ValueError, match="start and end"):
        use_case.execute("MSFT", start="2025-01-01")


def test_yfinance_adapter_normalizes_ticker_and_maps_rows(monkeypatch):
    calls = {}

    class FakeTicker:
        def __init__(self, ticker):
            calls["ticker"] = ticker

        def history(self, **kwargs):
            calls["kwargs"] = kwargs
            return pd.DataFrame(
                {"Close": [10.5], "Volume": [100]},
                index=pd.DatetimeIndex(["2025-01-02"], tz="UTC"),
            )

    monkeypatch.setattr(yfinance_module.yf, "Ticker", FakeTicker)
    result = YFinanceProvider().get_history(" aapl ", period="5d", interval="1h")

    assert calls == {
        "ticker": "AAPL",
        "kwargs": {"interval": "1h", "period": "5d", "auto_adjust": False},
    }
    assert result == PriceHistory(
        "AAPL", (PriceBar("2025-01-02T00:00:00+00:00", {"Close": 10.5, "Volume": 100.0}),)
    )


def test_yfinance_adapter_uses_date_range(monkeypatch):
    calls = {}

    class FakeTicker:
        def __init__(self, ticker):
            pass

        def history(self, **kwargs):
            calls.update(kwargs)
            return pd.DataFrame({"Close": []})

    monkeypatch.setattr(yfinance_module.yf, "Ticker", FakeTicker)
    YFinanceProvider().get_history("AAPL", start="2025-01-01", end="2025-01-10")

    assert calls == {
        "interval": "1d",
        "start": "2025-01-01",
        "end": "2025-01-10",
        "auto_adjust": False,
    }


def test_cache_corrupt_file_is_treated_as_a_miss(tmp_path: Path):
    cache = JsonFileHistoryCache(tmp_path)
    (tmp_path / "broken.json").write_text("not json", encoding="utf-8")

    assert cache.get("broken") is None
