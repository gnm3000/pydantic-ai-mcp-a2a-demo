from fastmcp import FastMCP
from mcp.types import CompletionArgument, PromptReference, ResourceTemplateReference

from experiment_mcp.interface.mcp_completions import (
    complete_ticker,
    register_completions,
    ticker_completions,
)


def test_prompt_completion_suggests_common_tickers_by_prefix():
    suggestions = ticker_completions(
        PromptReference(name="analyze_ticker"),
        CompletionArgument(name="ticker", value=" nV "),
    )

    assert suggestions == ["NVDA"]


def test_resource_template_completion_suggests_tickers():
    suggestions = ticker_completions(
        ResourceTemplateReference(uri="market://symbols/{ticker}/news"),
        CompletionArgument(name="ticker", value="a"),
    )

    assert suggestions == ["AAPL", "AMZN"]


def test_completion_ignores_unknown_components_and_arguments():
    ticker_argument = CompletionArgument(name="question", value="A")
    unknown_prompt = PromptReference(name="other_prompt")

    assert ticker_completions(unknown_prompt, ticker_argument) is None
    assert (
        ticker_completions(
            ResourceTemplateReference(uri="other://{ticker}"),
            CompletionArgument(name="ticker", value="A"),
        )
        is None
    )


def test_completion_handler_is_registered_with_fastmcp():
    app = FastMCP("test")

    register_completions(app)

    assert app._completion_handler is not None
    assert complete_ticker(
        PromptReference(name="analyze_ticker"),
        CompletionArgument(name="ticker", value="M"),
        context=None,
    ) == ["META", "MSFT"]
