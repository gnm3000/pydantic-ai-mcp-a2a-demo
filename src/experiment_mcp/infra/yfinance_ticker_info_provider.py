"""yfinance adapter for descriptive ticker information."""

import yfinance as yf

from experiment_mcp.core.models import TickerInfo


class YFinanceTickerInfoProvider:
    def get_ticker_info(self, ticker: str) -> TickerInfo:
        info = yf.Ticker(ticker).get_info()
        if not info:
            raise ValueError(f"No information found for ticker {ticker}.")
        return TickerInfo(
            ticker=ticker,
            name=self._first_string(info, "longName", "shortName"),
            exchange=self._string(info.get("fullExchangeName") or info.get("exchange")),
            currency=self._string(info.get("currency")),
            quote_type=self._string(info.get("quoteType")),
            sector=self._string(info.get("sector")),
            industry=self._string(info.get("industry")),
            country=self._string(info.get("country")),
            website=self._string(info.get("website")),
            summary=self._string(info.get("longBusinessSummary")),
        )

    @staticmethod
    def _first_string(info: dict, *keys: str) -> str | None:
        for key in keys:
            value = YFinanceTickerInfoProvider._string(info.get(key))
            if value:
                return value
        return None

    @staticmethod
    def _string(value: object) -> str | None:
        return value.strip() if isinstance(value, str) and value.strip() else None
