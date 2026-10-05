"""Adapter for additional read-only yfinance ticker data."""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

import yfinance as yf

from experiment_mcp.application.ports import TickerDataKind


class YFinanceTickerDataProvider:
    """Fetch ticker data and convert pandas/numpy values to JSON-compatible values."""

    def get_ticker_data(self, ticker: str, kind: TickerDataKind) -> object:
        symbol = yf.Ticker(ticker)
        if kind == "quote":
            result = dict(symbol.fast_info)
        elif kind == "recommendations":
            result = symbol.get_recommendations()
        elif kind == "calendar":
            result = symbol.get_calendar()
        elif kind == "news":
            result = symbol.get_news(count=5, tab="news")
        else:
            result = symbol.get_actions()
        return self._json_value(result)

    @classmethod
    def _json_value(cls, value: Any) -> Any:
        if value is None or value.__class__.__name__ in {"NAType", "NaTType"}:
            return None
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Mapping):
            return {str(key): cls._json_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._json_value(item) for item in value]
        if hasattr(value, "reset_index") and hasattr(value, "to_dict"):
            return cls._json_value(value.reset_index().to_dict(orient="records"))
        if hasattr(value, "item"):
            return cls._json_value(value.item())
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if hasattr(value, "to_dict"):
            return cls._json_value(value.to_dict())
        return str(value)
