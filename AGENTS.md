# Instructions for Coding Agents

Use this file to navigate the project. Read [the docs index](docs/README.md),
then the guide related to your task. Treat source code, `pyproject.toml`,
`uv.lock`, and tests as the source of truth when docs and implementation differ.

## Project facts

- Python 3.13; dependencies are managed with `uv` and locked in `uv.lock`.
- FastMCP is constrained to `>=4.0.10,<5`; this repository targets FastMCP 4.
- React uses TypeScript, Vite, and npm in `ui/`.
- The main MCP server is composed in `src/experiment_mcp/server_factory.py` and
  runs on port `8005`. The standalone CodeMode server runs on `8006`.
- The AG-UI/A2A backend is `src/experiment_mcp/agentic/a2a_web.py`; the React
  chat is served at `/a2a` on port `5178` under Docker Compose.

## Code organization

- `core/`: domain models and pure rules; keep framework and network code out.
- `application/`: use cases and ports that describe required dependencies.
- `infra/`: external providers and persistence adapters.
- `interface/`: FastMCP registrations and protocol-specific adapters.
- `agentic/`: agent orchestration and AG-UI/A2A endpoints.
- `examples/`: runnable learning examples; keep CLI/bootstrap concerns separate
  from agent logic where practical.
- `tests/`: deterministic tests using fakes; do not require external market or
  model-provider requests.

## Working conventions

- Keep documentation and user-facing software copy in English.
- Prefer the smallest change that fits the existing structure. Avoid adding
  abstractions without a concrete need.
- Use typed Python signatures and useful tool/resource descriptions. Keep
  credentials out of tool arguments, source, and logs.
- Keep the default MCP token local. Never commit `.env` or real credentials.
- Add tests for behavior changes and prefer fake providers over live APIs.
- Do not edit `uv.lock` by hand; use `uv add`, `uv remove`, or `uv lock`.
- When changing a protocol component, update the relevant guide under `docs/`.

## Validation commands

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
npm --prefix ui run lint
npm --prefix ui run build
```

For local service-level checks, use `docker compose up --build -d` and the URLs
listed in the root README. External agent calls need `OPENROUTER_API_KEY` and
can fail or vary with the model provider.
