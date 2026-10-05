"""Typer CLI for the Pydantic AI market agent."""

import asyncio
import os
from pathlib import Path
from typing import Annotated

import logfire
import typer
from dotenv import load_dotenv
from market_agent import run_agent

PROJECT_ROOT = Path(__file__).resolve().parents[1]
app = typer.Typer(help="Pydantic AI agent consuming the local market MCP.")


@app.command()
def main(
    ticker: Annotated[str, typer.Option(help="Ticker to read from the MCP resource.")] = "AAPL",
    question: Annotated[
        str, typer.Option(help="Question for the Pydantic AI agent.")
    ] = "Describe the company and analyze its recent price movement.",
) -> None:
    """Run the agent and print its answer."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        typer.echo("OPENROUTER_API_KEY is not set in .env or the environment.", err=True)
        raise typer.Exit(code=1)
    mcp_token = os.getenv("MCP_DEV_TOKEN")
    if not mcp_token:
        typer.echo("MCP_DEV_TOKEN is not set in .env or the environment.", err=True)
        raise typer.Exit(code=1)

    try:
        answer = asyncio.run(run_agent(ticker, question, api_key, mcp_token))
    except Exception as error:
        typer.echo(f"Could not run the agent: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(answer.model_dump_json(indent=2))


def bootstrap() -> None:
    """Load local configuration, configure console tracing, and start Typer."""
    load_dotenv(PROJECT_ROOT / ".env")
    logfire.configure(
        send_to_logfire=False,
        service_name="experiment-mcp-agent",
        console=logfire.ConsoleOptions(verbose=True, min_log_level="debug"),
    )
    logfire.instrument_pydantic_ai(include_content=False)
    app()


if __name__ == "__main__":
    bootstrap()
