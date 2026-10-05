# Architecture

MarketInsider separates market-data rules, use cases, external adapters, and
MCP registrations. The structure is small enough to follow while still showing
where responsibilities belong.

## Python package map

| Path | Responsibility | Example |
| --- | --- | --- |
| `src/experiment_mcp/core/` | Domain models and pure calculations | `PriceHistory`, trend calculations |
| `src/experiment_mcp/application/` | Use cases and dependency ports | `GetPriceHistory` |
| `src/experiment_mcp/infra/` | External data and cache adapters | yfinance providers, JSON cache |
| `src/experiment_mcp/interface/` | MCP protocol registrations | tools, resources, prompts, auth |
| `src/experiment_mcp/agentic/` | Agent protocols and web endpoints | AG-UI coordinator and A2A agents |
| `examples/` | Runnable clients and protocol demonstrations | Pydantic AI clients |
| `tests/` | Fast deterministic behavior checks | fake providers and MCP clients |

`server_factory.py` is the composition root for the main MCP server. It creates
the adapters and use cases, registers protocol components, and returns the
FastMCP server. `server.py` is the executable entry point. The CodeMode demo has
its own composition root in `code_mode_server.py` so its transformed tool
catalog does not replace the main server's direct tools.

## Market-data request flow

```text
MCP client
  → FastMCP interface
  → application use case
  → provider/cache port
  → yfinance adapter or JSON cache
```

The core and application layers do not depend on FastMCP or yfinance. The
application layer receives adapters through ports, which lets unit tests use
fakes. Historical price responses are cached as JSON for 15 minutes in
`.cache/market-data/`.

## Agent and UI flows

```text
React /a2a (:5178)
  → AG-UI /ag-ui (:8100)
  → Pydantic AI coordinator
      ├─ MCP CodeMode (:8006) for composed market-data operations
      └─ A2A specialists (:8100/fundamentals, /prices, /news)
          → main MCP server (:8005)
```

The coordinator has both the CodeMode MCP toolset and the specialist-delegation
tools available. The model chooses which capabilities to call, so a price
question may go to the Price Analyst without invoking CodeMode. CodeMode is
most useful when the requested work needs several MCP operations composed in a
single sandbox execution.

The React Price Explorer is also an MCP App. The `mcp-app-preview` Compose
service provides a local host at `http://localhost:8081`; it is separate from
the AG-UI chat.

## Boundaries and limitations

- The local bearer token is a development verifier, not a production identity
  system.
- CodeMode is experimental in FastMCP. Its server exposes only read-only market
  operations and sets explicit sandbox and tool-call limits.
- The A2A demo and market data use external services. Model selection,
  availability, data coverage, and latency can vary.
- The current GitHub Actions workflow runs Python lint/tests and React lint/
  build. It does not run a browser-driven E2E suite or call a live model.
