# Building a FastMCP Server

This guide follows the FastMCP 4 server in this repository. It focuses on the
decisions needed to add a capability while keeping domain logic testable.

## 1. Start from the repository's dependency contract

The project requires Python 3.13 and constrains FastMCP to
`>=4.0.10,<5`; `uv.lock` records the resolved versions. Install the locked
environment with:

```bash
uv sync --locked
```

Do not copy an API from a different FastMCP major version without checking its
documentation and behavior in the installed version.

## 2. Put behavior in the right layer

For a new market-data operation, keep pure calculations in `core/`, an
application use case and dependency port in `application/`, vendor or storage
code in `infra/`, and the `@mcp.tool`, `@mcp.resource`, or `@mcp.prompt`
registration in `interface/`. The root `server_factory.py` composes those
pieces.

Avoid putting the whole implementation in a decorator function. A small MCP
handler should translate protocol arguments to a use case and format the
result.

## 3. Define typed protocol contracts

FastMCP uses function annotations and docstrings to construct schemas and
descriptions. Prefer explicit argument and return types. This project opts into
strict input validation when constructing its servers:

```python
mcp = FastMCP("Example Server", strict_input_validation=True)

@mcp.tool
def lookup_record(record_id: int) -> dict[str, str | int]:
    """Return the public summary for a record identifier."""
    ...
```

Strict validation rejects mismatched JSON types instead of coercing values.
Test the inputs that clients are expected to send. Use `Context` only when a
handler needs request information such as request IDs. For blocking
synchronous libraries, FastMCP normally dispatches synchronous tools to a
worker thread; reserve `run_in_thread=False` for libraries that truly require
thread affinity.

## 4. Compose and run the server

The executable main server is `experiment-mcp` and uses Streamable HTTP on
port `8005`:

```bash
uv run experiment-mcp
```

For the full stack, copy `.env.example`, set a development `MCP_DEV_TOKEN`, and
run:

```bash
docker compose up --build -d
```

The CodeMode example is a separate FastMCP server on port `8006`; its dedicated
factory is in [`code_mode_server.py`](../src/experiment_mcp/code_mode_server.py).

## 5. Apply security boundaries

- Keep credentials in server configuration, not in model-visible tool
  arguments.
- The local token must contain at least 32 characters. It is intended for
  development, not as a substitute for a production identity provider.
- Validate types and domain constraints at the server boundary.
- Treat resource-template parameters as untrusted, especially when using them
  in paths or upstream URLs.
- Expose only the operations each server needs. CodeMode uses a separate,
  read-only tool catalog and a bounded sandbox.
- Keep logs useful but never log tokens or secrets.

## 6. Add a deterministic test

Construct use cases with fake ports and test observable behavior without
network access. Then test MCP registration/serialization with an in-process
FastMCP client. Existing examples are in `tests/test_market_data.py`,
`tests/test_mcp_resources.py`, and `tests/test_tools.py`.

Run the [development checks](testing-and-ci.md) before documenting the new
component. Link the guide to the implementation so future readers can inspect
the complete behavior.

Official references: [FastMCP tools](https://gofastmcp.com/servers/tools),
[resources](https://gofastmcp.com/servers/resources), and
[FastMCP installation](https://gofastmcp.com/getting-started/installation).
