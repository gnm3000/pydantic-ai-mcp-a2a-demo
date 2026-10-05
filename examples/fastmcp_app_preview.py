"""Bootstrap the MCP server for FastMCP's local Apps preview command."""

from experiment_mcp.bootstrap import load_environment

load_environment()

from experiment_mcp.server_factory import create_server  # noqa: E402

mcp = create_server(auth_required=False)
