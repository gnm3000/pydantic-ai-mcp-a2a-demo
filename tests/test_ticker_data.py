from datetime import date, datetime, timezone

import numpy as np
import pandas as pd
import pytest

import experiment_mcp.infra.yfinance_ticker_data_provider as data_module
from experiment_mcp.application.get_ticker_data import GetTickerData
from experiment_mcp.infra.yfinance_ticker_data_provider import (
    YFinanceTickerDataProvider,
)


class FakeTicker:
    def __init__(self, ticker):
        self.ticker = ticker
        self.fast_info = {"lastPrice": 12.5, "currency": "USD"}

    def get_recommendations(self):
        return pd.DataFrame({"strongBuy": [3]}, index=["0m"])

    def get_calendar(self):
        return {"Earnings Date": [date(2026, 10, 20)]}

    def get_news(self, *, count, tab):
        return [{"title": f"{count} {tab} headlines"}]

    def get_actions(self):
        return pd.DataFrame(
            {"Dividends": [0.25]}, index=[datetime(2026, 1, 1, tzinfo=timezone.utc)]
        )


@pytest.mark.parametrize("kind", ["quote", "recommendations", "calendar", "news", "actions"])
def test_provider_dispatches_to_yfinance_and_normalizes_results(monkeypatch, kind):
    monkeypatch.setattr(data_module.yf, "Ticker", FakeTicker)

    data = GetTickerData(YFinanceTickerDataProvider()).execute(" nvda ", kind)

    if kind == "quote":
        assert data == {"lastPrice": 12.5, "currency": "USD"}
    elif kind == "recommendations":
        assert data == [{"index": "0m", "strongBuy": 3}]
    elif kind == "calendar":
        assert data == {"Earnings Date": ["2026-10-20"]}
    elif kind == "news":
        assert data == [{"title": "5 news headlines"}]
    else:
        assert data == [{"index": "2026-01-01T00:00:00+00:00", "Dividends": 0.25}]


def test_get_ticker_data_rejects_empty_ticker():
    class UnusedProvider:
        def get_ticker_data(self, ticker, kind):
            raise AssertionError("provider must not be called")

    with pytest.raises(ValueError, match="cannot be empty"):
        GetTickerData(UnusedProvider()).execute("   ", "quote")


def test_json_value_normalizes_special_numeric_and_pandas_values():
    value = {
        "nan": float("nan"),
        "numpy": np.int64(7),
        "missing": pd.NA,
        "not_a_date": pd.NaT,
        "nested": (datetime(2026, 1, 2, tzinfo=timezone.utc), date(2026, 1, 3)),
    }

    assert YFinanceTickerDataProvider._json_value(value) == {
        "nan": None,
        "numpy": 7,
        "missing": None,
        "not_a_date": None,
        "nested": ["2026-01-02T00:00:00+00:00", "2026-01-03"],
    }


def test_json_value_handles_series_and_fallback_objects():
    assert YFinanceTickerDataProvider._json_value(pd.Series([1, 2], index=["a", "b"])) == [
        {"index": "a", "0": 1},
        {"index": "b", "0": 2},
    ]

    class CustomValue:
        def __str__(self):
            return "custom value"

    assert YFinanceTickerDataProvider._json_value(CustomValue()) == "custom value"
