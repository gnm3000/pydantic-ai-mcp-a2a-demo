"""Interactive client demo for FastMCP tasks, elicitation, and progress."""

import asyncio
import os
from typing import Annotated

import typer
from fastmcp import Client
from fastmcp_tasks import call_tool_task

from experiment_mcp.bootstrap import load_environment

app = typer.Typer(help="Demo MCP bearer auth, elicitation, task polling, and progress.")


async def handle_elicitation(message, response_type, params, context):
    """Ask for the requested fields in the local terminal and return the answers."""
    del response_type, context
    schema = getattr(params, "requested_schema", {})
    fields = schema.get("properties", {})
    answers = {}
    for name, definition in fields.items():
        choices = definition.get("enum")
        prompt = f"{message}\n{name}"
        if choices:
            prompt += f" ({' / '.join(choices)})"
        prompt += ": "
        while True:
            answer = await asyncio.to_thread(input, prompt)
            if not choices or answer in choices:
                answers[name] = answer
                break
            typer.echo(f"Choose a valid option: {', '.join(choices)}")
    return answers


async def show_progress(progress: float, total: float | None, message: str | None) -> None:
    """Render server-reported progress in the console."""
    amount = f"{progress:g}/{total:g}" if total is not None else f"{progress:g}"
    typer.echo(f"[{amount}] {message or 'Procesando'}")


async def run_demo(tickers: list[str], token: str) -> None:
    client = Client(
        "http://127.0.0.1:8005/mcp",
        auth=token,
        elicitation_handler=handle_elicitation,
        progress_handler=show_progress,
    )
    async with client:
        task = await call_tool_task(
            client,
            "analyze_multiple_tickers",
            {"tickers": tickers},
        )
        typer.echo(f"Tarea MCP iniciada: {task.task_id}")
        initial_status = await task.status()
        typer.echo(f"Estado: {initial_status.status}")
        result = await task.result()
        typer.echo("Resultado:")
        typer.echo(result.model_dump_json(indent=2))


@app.command()
def main(
    ticker: Annotated[
        list[str] | None, typer.Option("--ticker", help="Ticker symbol; repeat up to five times.")
    ] = None,
) -> None:
    """Start a multi-ticker task and display its protocol updates."""
    token = os.getenv("MCP_DEV_TOKEN")
    if not token:
        typer.echo("MCP_DEV_TOKEN is not set in .env or the environment.", err=True)
        raise typer.Exit(code=1)
    tickers = ticker or ["NVDA"]
    if not 1 <= len(tickers) <= 5:
        typer.echo("Provide between one and five tickers.", err=True)
        raise typer.Exit(code=2)

    try:
        asyncio.run(run_demo(tickers, token))
    except Exception as error:
        typer.echo(f"Could not run the MCP demo: {error}", err=True)
        raise typer.Exit(code=1) from error


def bootstrap() -> None:
    """Load project settings before starting Typer."""
    load_environment()
    app()


if __name__ == "__main__":
    bootstrap()
