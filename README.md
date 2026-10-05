# MarketInsider MCP

MarketInsider is an educational market-data project and a practical guide to
building MCP servers with FastMCP 4. It shows how to model server capabilities,
connect them to an AI agent, and test the integration without relying on live
market data in unit tests.

The server uses `yfinance` for market data and caches historical prices in
`.cache/market-data`. This is a learning project, not a trading system or
investment advice.

## What this project demonstrates

- FastMCP over Streamable HTTP, with typed tools, resources, resource templates,
  prompts, completions, and strict input validation.
- A read-only CodeMode server that lets an agent compose market-data tools in a
  bounded Python sandbox.
- A Pydantic AI client that reads MCP context and calls MCP tools.
- An AG-UI chat coordinator that can call MCP and delegate to A2A specialists.
- A React MCP App for exploring historical prices.
- Local bearer-token authentication, console-only observability, a JSON cache,
  and deterministic Python tests.

## Start here

### Requirements

- Python 3.13 or later and [uv](https://docs.astral.sh/uv/)
- Node.js 22 and npm for the React UI
- Docker Compose for the full demo stack (optional)
- An OpenRouter API key only for the agent and chat demos

### Run the MCP server

```bash
cp .env.example .env
uv run python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Put the generated value in `.env` as `MCP_DEV_TOKEN`. Add `OPENROUTER_API_KEY`
only if you plan to run an agent demo. Then install dependencies and launch the
authenticated MCP server:

```bash
uv sync --locked
uv run experiment-mcp
```

The Streamable HTTP endpoint is `http://localhost:8005/mcp`. The static token
verifier is for local development; use an identity provider and deployment
security controls for a public service.

### Run the full stack

With `.env` configured:

```bash
docker compose up --build -d
```

| Service | URL |
| --- | --- |
| Main MCP server | `http://localhost:8005/mcp` |
| CodeMode MCP server | `http://localhost:8006/mcp` |
| FastMCP App preview | `http://localhost:8081` |
| React AG-UI/A2A chat | `http://localhost:5178/a2a` |
| A2A specialist cards | `http://localhost:8100/{fundamentals,prices,news}` |

The App preview runs without bearer auth because its local host does not forward
the token. The MCP server itself remains authenticated.

## Documentation

The [documentation index](docs/README.md) has a suggested learning path for
agents and developers building MCP servers. Start with:

1. [Architecture](docs/architecture.md) to understand this repository.
2. [Designing MCP interfaces](docs/designing-mcp-interfaces.md) to choose
   between tools, resources, and prompts.
3. [Building a FastMCP server](docs/building-a-fastmcp-server.md) to follow the
   implementation and security patterns used here.
4. [Testing and CI](docs/testing-and-ci.md) to add reliable coverage.

Continue with [agents and A2A](docs/agents-and-a2a.md) or
[CodeMode](docs/code-mode.md) for agent integration patterns. The root
[`AGENTS.md`](AGENTS.md) gives coding agents project-specific navigation and
working instructions.

## When to use CodeMode

Use CodeMode when an answer needs several MCP calls joined into one workflow: fetch data, compare it, calculate a result, and return a concise summary. The model discovers the relevant tools, writes Python and FastMCP executes it in a sandbox. For example, one run can fetch NVDA prices for two periods, compare returns, and report the change without sending every intermediate row back to the model. This can reduce context use and model round-trips for data-heavy tasks. It is not always faster: discovery and execution add overhead, and upstream APIs may dominate latency. For one simple lookup, a direct tool call is clearer. CodeMode composes permitted tools; it does not replace resources or A2A delegation. This demo restricts execution to read-only market tools and explicit limits by design.

Based on the [FastMCP CodeMode documentation](https://gofastmcp.com/servers/transforms/code-mode).

## Run the agent examples

Start the MCP server and configure `.env`, then try the direct-tool Pydantic AI
agent:

```bash
uv run python examples/pydantic_ai_agent.py --ticker AAPL
uv run python examples/pydantic_ai_agent.py \
  --ticker NVDA \
  --question "Summarize the company and analyze its last five trading days."
```

The agent reads the `analyze_ticker` prompt, explicitly reads the ticker-profile
resource, and uses its structured `MarketAnalysis` output model.

The CodeMode agent connects to port `8006` and can compose price retrieval and
calculations inside one sandboxed execution:

```bash
uv run python examples/code_mode_cli.py --ticker NVDA --period 1mo
```

The multi-ticker protocol demo illustrates progress and elicitation. It accepts
up to five tickers and simulates 5–10 seconds of work per ticker:

```bash
uv run python examples/mcp_protocol_demo.py --ticker NVDA --ticker AAPL
```

## Development checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
npm --prefix ui ci
npm --prefix ui run lint
npm --prefix ui run build
```

Python coverage is enforced at 90% or higher. GitHub Actions runs Ruff and the
Python suite, plus the React lint and build checks. See
[testing and CI](docs/testing-and-ci.md) for what is and is not automated.

## Project structure

```text
src/experiment_mcp/
├── core/          # Domain models and pure analysis rules
├── application/   # Use cases and provider ports
├── infra/         # yfinance adapters and JSON history cache
├── interface/     # FastMCP tools, resources, prompts, and integrations
└── agentic/       # AG-UI coordinator and A2A specialist endpoints
```

The main MCP server listens on port `8005`; the separate CodeMode server listens
on `8006`. Both share the local market-data cache. CodeMode is experimental in
FastMCP and its exposed catalog is limited to read-only market operations with
explicit execution limits. The A2A demo uses an LLM provider and live market
data, so its behavior depends on those external services. See
[architecture](docs/architecture.md) and [CodeMode](docs/code-mode.md) for
details.
