from fastmcp import FastMCP
from fastmcp.server.middleware.logging import LoggingMiddleware
from fastmcp.server.middleware.timing import DetailedTimingMiddleware

from experiment_mcp.interface.mcp_observability import register_console_observability


def test_console_observability_logs_without_payloads():
    app = FastMCP("test")

    register_console_observability(app)

    logging = next(item for item in app.middleware if isinstance(item, LoggingMiddleware))
    timing = next(item for item in app.middleware if isinstance(item, DetailedTimingMiddleware))
    assert logging.include_payloads is False
    assert logging.logger.name == "experiment_mcp.mcp"
    assert timing.logger is logging.logger
