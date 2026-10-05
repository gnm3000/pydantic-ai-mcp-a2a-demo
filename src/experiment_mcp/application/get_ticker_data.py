"""Use case for reading additional yfinance data for a ticker."""

from experiment_mcp.application.ports import TickerDataKind, TickerDataProvider


class GetTickerData:
    def __init__(self, provider: TickerDataProvider) -> None:
        self.provider = provider

    def execute(self, ticker: str, kind: TickerDataKind) -> object:
        normalized_ticker = ticker.strip().upper()
        if not normalized_ticker:
            raise ValueError("Ticker cannot be empty.")
        return self.provider.get_ticker_data(normalized_ticker, kind)
