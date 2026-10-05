"""Reusable prompts exposed by the market MCP server."""

import json

from fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    @mcp.prompt(
        name="analyze_ticker",
        version="1.0",
        title="Analyze a ticker (1.0)",
        description=(
            "Prepare the original flat analysis request with ticker profile and skill URIs."
        ),
        tags={"market-data", "analysis"},
        meta={"contract": "flat", "team": "experiment-mcp"},
    )
    def analyze_ticker_v1(
        ticker: str,
        question: str = "Summarize the company and its recent market performance.",
    ) -> str:
        """Prepare the version 1 analysis request.

        Args:
            ticker: Public-market ticker symbol, for example NVDA or AAPL.
            question: The analysis request to include for the model.
        """
        return build_analyze_ticker_prompt_v1(ticker, question)

    @mcp.prompt(
        name="analyze_ticker",
        version="2.0",
        title="Analyze a ticker (2.0)",
        description=(
            "Prepare a nested analysis request with explicit profile and skill context references."
        ),
        tags={"market-data", "analysis"},
        meta={"contract": "nested-context", "team": "experiment-mcp"},
    )
    def analyze_ticker_v2(
        ticker: str,
        question: str = "Summarize the company and its recent market performance.",
    ) -> str:
        """Prepare the version 2 analysis request.

        Args:
            ticker: Public-market ticker symbol, for example NVDA or AAPL.
            question: The analysis request to include for the model.
        """
        return build_analyze_ticker_prompt_v2(ticker, question)


def build_analyze_ticker_prompt_v1(
    ticker: str,
    question: str = "Summarize the company and its recent market performance.",
) -> str:
    """Build the original flat payload for the ticker-analysis prompt."""
    symbol = _normalize_ticker(ticker)
    return json.dumps(
        {
            "ticker": symbol,
            "question": question,
            "profile_uri": f"market://symbols/{symbol}",
            "skill_uri": "skill://market-analysis/SKILL.md",
        },
        ensure_ascii=False,
        indent=2,
    )


def build_analyze_ticker_prompt_v2(
    ticker: str,
    question: str = "Summarize the company and its recent market performance.",
) -> str:
    """Build the current payload with context references grouped by purpose."""
    symbol = _normalize_ticker(ticker)
    return json.dumps(
        {
            "ticker": symbol,
            "question": question,
            "context": {
                "company_profile": {"uri": f"market://symbols/{symbol}"},
                "analysis_skill": {"uri": "skill://market-analysis/SKILL.md"},
            },
        },
        ensure_ascii=False,
        indent=2,
    )


def _normalize_ticker(ticker: str) -> str:
    symbol = ticker.strip().upper()
    if not symbol:
        raise ValueError("Ticker cannot be empty.")
    return symbol
