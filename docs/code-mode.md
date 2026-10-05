# CodeMode

CodeMode is a FastMCP server transform that replaces direct exposure of the
underlying tool catalog with discovery and execution meta-tools. The model
discovers relevant tools as needed, writes Python that calls them, and FastMCP
runs that code in a sandbox. In this project, the transformed catalog is served
separately on port `8006`; the direct-tool server on port `8005` remains
available.

## When it helps

Choose CodeMode when the answer requires composing multiple MCP operations:
retrieve several datasets, filter or compare them, calculate a result, and
return a compact summary. This can keep intermediate data out of repeated model
messages and reduce model round-trips. For a single lookup or a direct
operation, calling the corresponding tool is usually simpler. CodeMode adds
discovery and execution overhead, so it is not guaranteed to be faster.

For example, a price analysis could fetch two ticker windows, calculate their
returns, compare the windows, and return only the summary. FastMCP CodeMode
documents its discovery/execution flow and recommends choosing discovery
patterns based on catalog size and schema complexity.

## This repository's setup

The server is assembled in [`code_mode_server.py`](../src/experiment_mcp/code_mode_server.py)
and registers a curated catalog in
[`mcp_code_mode.py`](../src/experiment_mcp/interface/mcp_code_mode.py):

- `get_price_history`
- `summarize_prices`
- `compare_price_windows`
- `weighted_window_trend`

FastMCP 4 is installed with the `code-mode` extra. The server uses the Monty
sandbox with a 15-second duration limit, 50 MB memory limit, recursion depth
100, and at most eight underlying tool calls per execution. The exposed tools
are read-only. The exact controls are set in the server factory and covered by
[`test_code_mode_server.py`](../tests/test_code_mode_server.py).

Run the service with Docker Compose or start the stack and ask the Pydantic AI
client to connect:

```bash
docker compose up --build -d code-mode-server
uv run python examples/code_mode_cli.py --ticker NVDA --period 1mo
```

The AG-UI coordinator also has a CodeMode toolset. It chooses dynamically
between CodeMode and A2A specialists; a question mentioning prices does not
guarantee that `execute` will be called. Check the UI delegation trace and
server logs to see which route ran.

## Tradeoffs and safety

- Discovery can require extra model calls; targeted discovery can save context
  when catalogs are large.
- One `execute` request can make multiple backend calls, so cap calls and
  execution resources.
- Keep the allow-listed MCP catalog narrow. Sandbox generated code and do not
  expose filesystem, shell, unrestricted network, or side-effecting tools for
  this example.
- Treat tool results as untrusted data and validate normal tool inputs and
  outputs as usual.
- CodeMode is experimental in FastMCP; recheck official docs and the pinned
  FastMCP version before relying on its API.

See the [official CodeMode guide](https://gofastmcp.com/servers/transforms/code-mode)
for current configuration details.
