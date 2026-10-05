"""Interfaces required by application use cases."""

from typing import Literal, Protocol

from experiment_mcp.core.models import PriceHistory, TickerInfo


class MarketDataProvider(Protocol):
    def get_history(
        self,
        ticker: str,
        *,
        period: str = "1mo",
        interval: str = "1d",
        start: str | None = None,
        end: str | None = None,
    ) -> PriceHistory: ...


class HistoryCache(Protocol):
    def get(self, key: str) -> PriceHistory | None: ...

    def set(self, key: str, history: PriceHistory) -> None: ...


class TickerInfoProvider(Protocol):
    def get_ticker_info(self, ticker: str) -> TickerInfo: ...


TickerDataKind = Literal["quote", "recommendations", "calendar", "news", "actions"]


class TickerDataProvider(Protocol):
    def get_ticker_data(self, ticker: str, kind: TickerDataKind) -> object: ...
