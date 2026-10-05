"""Domain models independent from market-data libraries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PriceBar:
    timestamp: str
    values: dict[str, float | None]


@dataclass(frozen=True)
class PriceHistory:
    ticker: str
    bars: tuple[PriceBar, ...]


@dataclass(frozen=True)
class TickerInfo:
    ticker: str
    name: str | None
    exchange: str | None
    currency: str | None
    quote_type: str | None
    sector: str | None
    industry: str | None
    country: str | None
    website: str | None
    summary: str | None
