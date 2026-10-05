"""Entry point for the authenticated CodeMode demonstration server."""

import os
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.experimental.transforms.code_mode import CodeMode, MontySandboxProvider
from fastmcp.server.auth import AuthProvider

from experiment_mcp.application.get_price_history import GetPriceHistory
from experiment_mcp.infra.json_history_cache import JsonFileHistoryCache
from experiment_mcp.infra.yfinance_provider import YFinanceProvider
from experiment_mcp.interface.mcp_auth import create_local_auth
from experiment_mcp.interface.mcp_code_mode import register_code_mode_tools
from experiment_mcp.interface.mcp_observability import register_console_observability

HOST = "0.0.0.0"
PORT = 8006
SANDBOX_LIMITS = {
    "max_duration_secs": 15,
    "max_memory": 50_000_000,
    "max_recursion_depth": 100,
}
MAX_TOOL_CALLS = 8


def create_code_mode_server(
    *,
    auth_required: bool = True,
    get_price_history: GetPriceHistory | None = None,
) -> FastMCP:
    """Compose the separate CodeMode server with only read-only market tools."""
    auth: AuthProvider | None = (
        create_local_auth(os.getenv("MCP_DEV_TOKEN")) if auth_required else None
    )
    code_mode = CodeMode(
        sandbox_provider=MontySandboxProvider(limits=SANDBOX_LIMITS),
        max_tool_calls=MAX_TOOL_CALLS,
    )
    server = FastMCP(
        "Market Data CodeMode Demo",
        strict_input_validation=True,
        auth=auth,
        transforms=[code_mode],
    )
    register_console_observability(server)

    if get_price_history is None:
        project_root = Path(__file__).resolve().parents[2]
        get_price_history = GetPriceHistory(
            provider=YFinanceProvider(),
            cache=JsonFileHistoryCache(project_root / ".cache" / "market-data"),
        )
    register_code_mode_tools(server, get_price_history)
    return server


def main() -> None:
    """Load local settings and serve CodeMode over Streamable HTTP."""
    from experiment_mcp.bootstrap import load_environment

    load_environment()
    create_code_mode_server().run(transport="http", host=HOST, port=PORT)
