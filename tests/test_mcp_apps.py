"""Tests for serving the built MCP App resource."""

import asyncio
from pathlib import Path

import pytest
from fastmcp import FastMCP

from experiment_mcp.interface.mcp_apps import register_market_app
from experiment_mcp.interface.mcp_tools import MARKET_APP_URI


def test_market_app_resource_returns_built_html(tmp_path: Path):
    bundle = tmp_path / "index.html"
    bundle.write_text("<html>market chart</html>", encoding="utf-8")
    server = FastMCP("test")
    register_market_app(server, bundle)
    resource = asyncio.run(server.get_resource(MARKET_APP_URI))

    assert resource.fn() == "<html>market chart</html>"


def test_market_app_resource_explains_missing_build(tmp_path: Path):
    server = FastMCP("test")
    register_market_app(server, tmp_path / "missing.html")
    resource = asyncio.run(server.get_resource(MARKET_APP_URI))

    with pytest.raises(RuntimeError, match="has not been built"):
        resource.fn()
