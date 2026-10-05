# Testing and CI

The project tests application behavior with fakes and runs protocol and
frontend checks in GitHub Actions. Keep unit tests independent of yfinance,
OpenRouter, and live MCP services.

## Python tests

Run:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Pytest configuration in `pyproject.toml` measures `experiment_mcp` and fails
below 90% coverage. Tests use fake providers and caches; add cases for success,
invalid inputs, and upstream failures. Keep assertions focused on public
behavior rather than implementation details.

For protocol-level behavior, use FastMCP's in-process `Client` with a composed
server. `tests/test_code_mode_server.py` demonstrates deterministic tool
execution without contacting yfinance.

## React checks

From the repository root:

```bash
npm --prefix ui ci
npm --prefix ui run lint
npm --prefix ui run build
```

The production build embeds the React MCP App bundle. A successful TypeScript
build checks the UI's static types as well.

## What CI currently covers

`.github/workflows/ci.yml` has separate Python and UI jobs. The Python job
installs the locked dependencies, runs Ruff, and runs pytest with the coverage
gate. The UI job installs with `npm ci`, runs ESLint, and builds the app.

CI does not currently launch Docker Compose, run browser-driven E2E/BDD
scenarios, or make live model/provider calls. Those checks would require
additional service orchestration and should use a deterministic mock model for
the normal CI path. Keep live provider smoke tests separate from the required
offline suite.

## Adding a check

1. Identify whether the behavior belongs to a pure unit test, an in-process MCP
   integration test, or a browser-level test.
2. Use fixtures or fakes so the default CI path is reproducible.
3. Add any required command to the relevant GitHub Actions job.
4. Update this guide when the CI contract changes.
