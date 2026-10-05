# FastMCP CodeMode Demo Endpoint

**Status: Implemented.** The project now includes a separate authenticated
CodeMode endpoint on port `8006`, a read-only market tool catalog, a sandboxed
execution example, and a Pydantic AI client. This plan remains as an
implementation record and acceptance checklist.

## Verification

- FastMCP `4.0.10` CodeMode imports, transforms the catalog, and executes a
  sandboxed tool call.
- `uv run ruff check .` and `uv run ruff format --check .` pass.
- `uv run pytest` passes with 94 tests and 99.04% coverage.
- `npm --prefix ui run build` succeeds.
- `docker compose config --quiet` succeeds.

## Goal

Add a separate, educational MCP endpoint that demonstrates FastMCP CodeMode:
an agent discovers available tools and writes sandboxed Python to combine
read-only market operations. Keep the existing MCP endpoint and its current
tool catalog unchanged.

## Why a separate endpoint

CodeMode presents meta-tools such as `search`, `get_schema`, and `execute` in
place of the underlying tools. A dedicated endpoint lets us demonstrate this
interaction without changing the tool surface used by the existing agent,
MCP App, task demo, or other clients.

## Implementation Plan

### 1. Confirm FastMCP CodeMode compatibility

- Review the CodeMode API supported by the FastMCP 4 version resolved in
  `uv.lock`.
- Confirm the documented import path, sandbox extra, default limits, and
  transform behavior against the pinned dependency.
- Keep FastMCP on the existing v4 version range; do not upgrade unrelated
  dependencies as part of this example.

### 2. Add the CodeMode dependency

- Add the required FastMCP sandbox extra with `uv add` and update `uv.lock`.
- Avoid adding a second FastMCP installation or a separate sandbox runtime
  unless the official package requires it.
- Verify that the existing React Apps preview still builds with the resolved
  dependency set.

### 3. Create a dedicated server factory and endpoint

- Add a `code_mode_server` module and a separate CLI entry point or documented
  command that starts it on a different local port, such as `8006`.
- Protect the endpoint with the same local bearer-token configuration used by
  the main MCP server.
- Apply FastMCP's `CodeMode` transform only to this server.
- Register a small, curated catalog of read-only operations, initially:
  - fetch historical ticker prices;
  - summarize a price series;
  - compare two price windows.
- Reuse the existing application use cases and infrastructure adapters rather
  than duplicating market-data logic.

### 4. Set conservative execution limits

- Use the sandbox provider documented by the installed FastMCP version.
- Set explicit limits for execution duration, memory, and tool calls per
  `execute` invocation.
- Keep the code sandbox limited to the exposed MCP tools. Do not expose shell,
  filesystem, arbitrary network, trading, or other side-effecting operations.
- Treat generated code and all returned market data as untrusted input.

### 5. Add a client example

- Add a small Pydantic AI example that connects specifically to the CodeMode
  endpoint.
- Let the model discover the read-only catalog and combine calls through
  CodeMode's `execute` tool.
- Return a typed market-analysis result and report data limitations instead of
  inventing unavailable values.
- Keep the existing agent example connected to the original endpoint so both
  direct tool use and CodeMode orchestration remain easy to compare.

### 6. Add tests

- Unit-test CodeMode server construction, auth, and the curated tool catalog.
- Test a representative composed workflow, such as fetching NVDA history and
  returning its summary through a sandboxed `execute` call.
- Test invalid tool names, malformed code, execution limits, and tool-call
  failures.
- Use fake providers and deterministic fixtures; tests must not need market
  network access or API credentials.
- Add an optional local integration command for manually exercising the
  endpoint with a real MCP client.

### 7. Document and validate

- Document both MCP URLs, startup commands, token setup, and the difference
  between direct tool calls and CodeMode in the root README.
- Add Ruff and test commands to the development instructions if they are not
  already present.
- Update GitHub Actions to run Ruff and the Python test suite, including the
  configured coverage threshold.
- Validate with `uv run ruff check .` and `uv run pytest`.

## Acceptance Criteria

- The original MCP endpoint, direct tools, task/elicitation demo, and MCP App
  continue to work without CodeMode behavior changes.
- The new endpoint requires the local bearer token and exposes CodeMode's
  discovery and execution tools.
- An agent can use the new endpoint to compose at least two read-only market
  operations and return a structured result.
- Sandbox limits and the allow-listed tool surface are explicit and covered by
  tests.
- CI passes Ruff, all Python tests, and the required coverage threshold.
- The README explains how to start and compare both endpoints.

## Out of Scope

- Replacing the existing endpoint with CodeMode.
- Enabling generated code to access arbitrary host commands, files, or
  unrestricted network connections.
- Adding trading, order placement, or other write operations.
- Adding a public deployment or production identity provider for this demo.

## Reference

- [FastMCP CodeMode documentation](https://gofastmcp.com/servers/transforms/code-mode)
