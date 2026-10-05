"""Typer CLI bootstrap for the CodeMode Pydantic AI example."""

import asyncio
import os
from typing import Annotated

import typer
from code_mode_agent import run_code_mode_agent

from experiment_mcp.bootstrap import load_environment

app = typer.Typer(help="Run the Pydantic AI agent against the CodeMode MCP server.")


@app.command()
def main(
    ticker: Annotated[str, typer.Option(help="Ticker symbol to analyze.")] = "AAPL",
    period: Annotated[str, typer.Option(help="History period, such as 5d or 1mo.")] = "1mo",
) -> None:
    """Run the CodeMode agent and print its structured response."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    token = os.getenv("MCP_DEV_TOKEN")
    if not api_key:
        typer.echo("OPENROUTER_API_KEY is not set in .env or the environment.", err=True)
        raise typer.Exit(code=1)
    if not token:
        typer.echo("MCP_DEV_TOKEN is not set in .env or the environment.", err=True)
        raise typer.Exit(code=1)

    try:
        result = asyncio.run(run_code_mode_agent(ticker, period, api_key, token))
    except Exception as error:
        typer.echo(f"Could not run the CodeMode agent: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(result.model_dump_json(indent=2))


def bootstrap() -> None:
    """Load project settings and invoke the CLI."""
    load_environment()
    app()


if __name__ == "__main__":
    bootstrap()
