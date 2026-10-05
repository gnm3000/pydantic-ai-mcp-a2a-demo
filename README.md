# Market Intelligence MCP

A portfolio project exploring how AI agents can access market data through the
Model Context Protocol (MCP). It combines a FastMCP HTTP server, a Pydantic AI
client, an AG-UI chat with A2A specialist agents, and a small React MCP App.

The current market-data adapter uses `yfinance` and caches historical price
responses locally. This is an educational demo, not a trading system or a
source of investment advice.

## Features

- FastMCP server over Streamable HTTP with bearer-token authentication and
  strict input validation.
- Price-analysis tools, historical OHLCV retrieval, JSON caching, ticker
  resources, versioned prompts, a market-analysis skill, and ticker completions.
- Long-running multi-ticker task demo with progress updates and elicitation.
- Pydantic AI example that reads MCP resources and calls MCP tools.
- React MCP App for price charts and an AG-UI chat that delegates work to three
  A2A specialists: company fundamentals, price analysis, and market news.
- Console-only request logging and Pydantic AI tracing; trace content is not
  exported to an external observability service.

## Requirements

- Python 3.13 or later
- [uv](https://docs.astral.sh/uv/)
- Node.js and npm (for the React app)
- Docker Compose (optional)
- An OpenRouter API key (only for the Pydantic AI and AG-UI demos)

## Run locally

Create a local environment file and generate a development token:

```bash
cp .env.example .env
uv run python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Set the generated value as `MCP_DEV_TOKEN` in `.env`. Set
`OPENROUTER_API_KEY` there only if you plan to use an agent demo. The `.env`
file is ignored by Git.

Install Python dependencies and start the MCP server:

```bash
uv sync --locked
uv run experiment-mcp
```

The authenticated Streamable HTTP endpoint is `http://localhost:8000/mcp`.
This static bearer token is intended for local development; use an appropriate
identity provider and deployment security controls for a public service.

## React MCP App

Build the app bundle before launching the MCP server:

```bash
npm --prefix ui ci
npm --prefix ui run build
```

The app is exposed as a `ui://` resource and opened by the `open_price_chart`
tool in an MCP Apps-compatible host. FastMCP's local preview is also available:

```bash
uv run fastmcp dev apps examples/fastmcp_app_preview.py
```

For the complete local stack, configure `.env` and run:

```bash
docker compose up --build
```

- MCP server: `http://localhost:8000/mcp`
- FastMCP App preview: `http://localhost:8081`
- AG-UI/A2A chat: `http://localhost:5173/a2a`
- A2A specialist agent cards: `/fundamentals`, `/prices`, and `/news` on port
  `8100`

The FastMCP App preview uses a local development server without bearer auth
because that preview does not forward the token. The MCP server itself remains
authenticated.

## Agent examples

With the MCP server running and `.env` configured, run the Pydantic AI agent:

```bash
uv run python examples/pydantic_ai_agent.py --ticker AAPL
uv run python examples/pydantic_ai_agent.py \
  --ticker NVDA \
  --question "Summarize the company and analyze its last five trading days."
```

The agent reads the `analyze_ticker` MCP prompt, ticker-profile resource, and
`market-analysis` skill. It receives MCP tools through `MCPToolset`; resources
are read explicitly by the client and supplied as context. Its structured
response uses the `MarketAnalysis` Pydantic model.

To demonstrate MCP tasks, progress, and elicitation, start the MCP server and
run:

```bash
uv run python examples/mcp_protocol_demo.py --ticker NVDA --ticker AAPL
```

The demo accepts up to five tickers and simulates 5–10 seconds of work for each
one.

## Architecture

```text
src/experiment_mcp/
├── core/          # Domain models and pure analysis rules
├── application/   # Use cases and provider ports
├── infra/         # yfinance adapters and JSON history cache
├── interface/     # FastMCP tools, resources, prompts, and apps
└── agentic/       # AG-UI coordinator and A2A specialist endpoints
```

Price-history responses are cached for 15 minutes in `.cache/market-data/`.
Cache keys include the ticker and requested period or date range and interval.
The cache and local secrets are excluded from Git.

## Development checks

```bash
uv run ruff check .
uv run pytest
npm --prefix ui run lint
npm --prefix ui run build
```

Python tests enforce a 90% coverage threshold. GitHub Actions runs the Python
suite and the React lint/build checks on pushes and pull requests.

## Project status and scope

This repository is a learning and portfolio project. It demonstrates MCP
primitives and agent communication; it does not implement the MCP code-execution
capability or provide a production-grade market-data service. Market data is
provided by `yfinance`, so availability and coverage depend on that upstream
source. See the official [Pydantic AI OpenRouter documentation](https://ai.pydantic.dev/models/openrouter/)
for provider configuration details.
