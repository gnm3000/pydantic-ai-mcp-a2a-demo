"""Use case for reading descriptive information about a ticker."""

from experiment_mcp.application.ports import TickerInfoProvider
from experiment_mcp.core.models import TickerInfo


class GetTickerInfo:
    def __init__(self, provider: TickerInfoProvider) -> None:
        self.provider = provider

    def execute(self, ticker: str) -> TickerInfo:
        normalized_ticker = ticker.strip().upper()
        if not normalized_ticker:
            raise ValueError("Ticker cannot be empty.")
        return self.provider.get_ticker_info(normalized_ticker)
