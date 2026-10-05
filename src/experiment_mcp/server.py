"""FastMCP HTTP server entry point."""

from experiment_mcp.server_factory import create_server

mcp = create_server()


def main() -> None:
    """Start the MCP server over Streamable HTTP."""
    mcp.run(transport="http", host="0.0.0.0", port=8005)
