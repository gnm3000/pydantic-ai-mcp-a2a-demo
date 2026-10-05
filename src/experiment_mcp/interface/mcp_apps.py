"""Resources backing MCP App user interfaces."""

from pathlib import Path

from fastmcp import FastMCP
from fastmcp.apps import AppConfig

from experiment_mcp.interface.mcp_tools import MARKET_APP_URI


def register_market_app(mcp: FastMCP, html_path: Path) -> None:
    """Expose the Vite-built single-file React app as an MCP UI resource."""

    @mcp.resource(
        uri=MARKET_APP_URI,
        name="Market price chart UI",
        description="Interactive React chart for exploring historical ticker prices.",
        tags={"market-data", "ui"},
        meta={"framework": "react", "build": "vite"},
        app=AppConfig(),
    )
    def market_chart_ui() -> str:
        """Return the embedded React bundle used by the market chart app."""
        try:
            return html_path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise RuntimeError(
                "The MCP App has not been built. Run `npm --prefix ui run build`."
            ) from error
