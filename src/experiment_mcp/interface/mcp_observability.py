"""Console-only request logging and timing middleware for the MCP server."""

import logging
import sys

from fastmcp import FastMCP
from fastmcp.server.middleware.logging import LoggingMiddleware
from fastmcp.server.middleware.timing import DetailedTimingMiddleware


def register_console_observability(mcp: FastMCP) -> None:
    """Log MCP operations and durations to stdout without logging payloads."""
    logger = logging.getLogger("experiment_mcp.mcp")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)

    mcp.add_middleware(LoggingMiddleware(logger=logger, include_payloads=False))
    mcp.add_middleware(DetailedTimingMiddleware(logger=logger))
