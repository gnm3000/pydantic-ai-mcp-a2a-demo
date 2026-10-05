"""Use case for retrieving and caching historical prices."""

import hashlib
import json

from experiment_mcp.application.ports import HistoryCache, MarketDataProvider
from experiment_mcp.core.models import PriceHistory


class GetPriceHistory:
    def __init__(self, provider: MarketDataProvider, cache: HistoryCache) -> None:
        self.provider = provider
        self.cache = cache

    def execute(
        self,
        ticker: str,
        *,
        period: str = "1mo",
        interval: str = "1d",
        start: str | None = None,
        end: str | None = None,
    ) -> PriceHistory:
        if (start is None) != (end is None):
            raise ValueError("start and end must be provided together.")

        normalized_ticker = ticker.strip().upper()
        cache_key = self._cache_key(normalized_ticker, period, interval, start, end)
        cached_history = self.cache.get(cache_key)
        if cached_history is not None:
            return cached_history

        history = self.provider.get_history(
            normalized_ticker,
            period=period,
            interval=interval,
            start=start,
            end=end,
        )
        self.cache.set(cache_key, history)
        return history

    @staticmethod
    def _cache_key(
        ticker: str, period: str, interval: str, start: str | None, end: str | None
    ) -> str:
        request = {
            "ticker": ticker,
            "period": period if start is None else None,
            "interval": interval,
            "start": start,
            "end": end,
        }
        serialized_request = json.dumps(request, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized_request.encode()).hexdigest()
