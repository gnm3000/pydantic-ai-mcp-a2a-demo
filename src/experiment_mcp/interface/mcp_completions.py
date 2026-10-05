"""Ticker argument suggestions for MCP prompts and resource templates."""

from fastmcp import FastMCP
from mcp.types import (
    CompletionArgument,
    CompletionContext,
    PromptReference,
    ResourceTemplateReference,
)

COMMON_TICKERS = (
    "AAPL",
    "AMZN",
    "GOOGL",
    "META",
    "MSFT",
    "NVDA",
    "TSLA",
)

TICKER_RESOURCE_TEMPLATES = {
    "market://symbols/{ticker}",
    "market://symbols/{ticker}/quote",
    "market://symbols/{ticker}/recommendations",
    "market://symbols/{ticker}/calendar",
    "market://symbols/{ticker}/news",
    "market://symbols/{ticker}/actions",
}


def register_completions(mcp: FastMCP) -> None:
    mcp.completion(complete_ticker)


def complete_ticker(
    ref: PromptReference | ResourceTemplateReference,
    argument: CompletionArgument,
    context: CompletionContext | None = None,
) -> list[str] | None:
    """Suggest common tickers for the analysis prompt and market resources."""
    del context  # Ticker suggestions do not depend on other arguments.
    return ticker_completions(ref, argument)


def ticker_completions(
    ref: PromptReference | ResourceTemplateReference,
    argument: CompletionArgument,
) -> list[str] | None:
    """Return matching common tickers for a supported ticker argument."""
    if argument.name != "ticker" or not _supports_ticker_reference(ref):
        return None

    prefix = argument.value.strip().upper()
    return [ticker for ticker in COMMON_TICKERS if ticker.startswith(prefix)]


def _supports_ticker_reference(
    ref: PromptReference | ResourceTemplateReference,
) -> bool:
    if isinstance(ref, PromptReference):
        return ref.name == "analyze_ticker"
    return ref.uri in TICKER_RESOURCE_TEMPLATES
