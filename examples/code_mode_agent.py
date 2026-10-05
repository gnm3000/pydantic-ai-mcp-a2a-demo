"""Pydantic AI agent that consumes the dedicated FastMCP CodeMode server."""

from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.messages import ToolCallPart
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

CODE_MODE_MCP_URL = "http://127.0.0.1:8001/mcp"
MODEL_NAME = "nvidia/nemotron-3-ultra-550b-a55b:free"


class PriceSummary(BaseModel):
    """Price statistics calculated from historical market data."""

    observations: int = Field(description="Number of historical closing prices analyzed.")
    minimum: float = Field(description="Lowest closing price in the requested period.")
    maximum: float = Field(description="Highest closing price in the requested period.")
    average: float = Field(description="Average closing price in the requested period.")


class CodeModeAnalysis(BaseModel):
    """Educational market analysis grounded in CodeMode tool results."""

    ticker: str = Field(description="The normalized market ticker symbol.")
    summary: str = Field(description="Concise analysis based on the retrieved price data.")
    price_summary: PriceSummary | None = Field(
        description="Calculated price statistics, or null when history is unavailable."
    )
    limitations: list[str] = Field(
        description="Missing data, uncertainty, or limitations relevant to the result."
    )


async def run_code_mode_agent(
    ticker: str,
    period: str,
    api_key: str,
    mcp_token: str,
) -> CodeModeAnalysis:
    """Ask an agent to analyze a ticker using the CodeMode MCP endpoint."""
    symbol = ticker.strip().upper()
    if not symbol:
        raise ValueError("Ticker cannot be empty.")

    model = OpenRouterModel(MODEL_NAME, provider=OpenRouterProvider(api_key=api_key))
    toolset = MCPToolset(CODE_MODE_MCP_URL, auth=mcp_token)
    agent = Agent(model, toolsets=[toolset], output_type=CodeModeAnalysis)

    @agent.output_validator
    def require_code_execution(ctx: RunContext[None], output: CodeModeAnalysis) -> CodeModeAnalysis:
        """Require the response to be grounded in a CodeMode execution."""
        used_execute = any(
            isinstance(part, ToolCallPart) and part.tool_name.endswith("execute")
            for message in ctx.messages
            for part in getattr(message, "parts", [])
        )
        if not used_execute:
            raise ModelRetry("Run a CodeMode workflow before returning the market analysis.")
        return output

    async with agent:
        result = await agent.run(
            f"Analyze {symbol} over the {period} period using historical closing prices."
        )
    return result.output
