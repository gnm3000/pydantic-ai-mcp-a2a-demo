"""Composition root for authenticated and local-preview MCP servers."""

import os
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.auth import AuthProvider
from fastmcp.server.providers.skills import SkillsDirectoryProvider
from fastmcp_tasks import TasksExtension

from experiment_mcp.application.get_price_history import GetPriceHistory
from experiment_mcp.application.get_ticker_data import GetTickerData
from experiment_mcp.application.get_ticker_info import GetTickerInfo
from experiment_mcp.infra.json_history_cache import JsonFileHistoryCache
from experiment_mcp.infra.yfinance_provider import YFinanceProvider
from experiment_mcp.infra.yfinance_ticker_data_provider import (
    YFinanceTickerDataProvider,
)
from experiment_mcp.infra.yfinance_ticker_info_provider import (
    YFinanceTickerInfoProvider,
)
from experiment_mcp.interface.mcp_apps import register_market_app
from experiment_mcp.interface.mcp_auth import create_local_auth
from experiment_mcp.interface.mcp_completions import register_completions
from experiment_mcp.interface.mcp_observability import register_console_observability
from experiment_mcp.interface.mcp_prompts import register_prompts
from experiment_mcp.interface.mcp_resources import register_resources
from experiment_mcp.interface.mcp_tools import register_tools


def create_server(*, auth_required: bool = True) -> FastMCP:
    """Compose the MCP server, optionally without auth for local app preview."""
    auth: AuthProvider | None = (
        create_local_auth(os.getenv("MCP_DEV_TOKEN")) if auth_required else None
    )
    server = FastMCP("MarketInsider Price Tools", strict_input_validation=True, auth=auth)
    server.add_extension(TasksExtension())
    register_console_observability(server)

    project_root = Path(__file__).resolve().parents[2]
    price_history = GetPriceHistory(
        provider=YFinanceProvider(),
        cache=JsonFileHistoryCache(project_root / ".cache" / "market-data"),
    )
    get_ticker_info = GetTickerInfo(YFinanceTickerInfoProvider())
    register_tools(server, price_history, get_ticker_info)
    register_market_app(server, project_root / "ui" / "dist" / "index.html")
    register_resources(
        server,
        get_ticker_info,
        GetTickerData(YFinanceTickerDataProvider()),
    )
    server.add_provider(SkillsDirectoryProvider(roots=project_root / "skills"))
    register_prompts(server)
    register_completions(server)
    return server
