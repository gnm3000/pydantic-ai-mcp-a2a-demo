"""yfinance adapter implementing the market-data application port."""

from __future__ import annotations

import math

import pandas as pd
import yfinance as yf

from experiment_mcp.core.models import PriceBar, PriceHistory


class YFinanceProvider:
    def get_history(
        self,
        ticker: str,
        *,
        period: str = "1mo",
        interval: str = "1d",
        start: str | None = None,
        end: str | None = None,
    ) -> PriceHistory:
        request: dict[str, str] = {"interval": interval}
        if start is not None and end is not None:
            request.update(start=start, end=end)
        else:
            request["period"] = period

        frame = yf.Ticker(ticker.strip().upper()).history(**request, auto_adjust=False)
        bars = tuple(self._to_price_bar(timestamp, row) for timestamp, row in frame.iterrows())
        return PriceHistory(ticker=ticker.strip().upper(), bars=bars)

    @staticmethod
    def _to_price_bar(timestamp: object, row: pd.Series) -> PriceBar:
        values = {}
        for column, value in row.items():
            number = float(value)
            values[str(column)] = number if math.isfinite(number) else None
        return PriceBar(timestamp=timestamp.isoformat(), values=values)
