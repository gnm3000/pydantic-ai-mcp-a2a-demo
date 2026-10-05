"""Application bootstrap: load local environment before importing the server."""

from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_environment() -> None:
    """Load project-local settings for command-line entry points."""
    load_dotenv(PROJECT_ROOT / ".env")


def main() -> None:
    """Load settings and start the FastMCP HTTP server."""
    load_environment()

    from experiment_mcp.server import main as run_server

    run_server()
