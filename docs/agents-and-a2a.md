# Agents, MCP, AG-UI, and A2A

This repository demonstrates two related but distinct connections: an agent
consuming MCP capabilities, and a coordinator delegating work to peer agents
over A2A while streaming a chat to React through AG-UI.

## Pydantic AI consumes MCP

`MCPToolset` connects a Pydantic AI agent to an MCP server. The direct example
uses the MCP endpoint on port `8005`; the CodeMode agent uses the separate
endpoint on `8006`.

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset

toolset = MCPToolset("http://localhost:8005/mcp", auth=mcp_token)
agent = Agent(model, toolsets=[toolset], output_type=MarketAnalysis)
```

Use the agent/toolset async context manager when you want to explicitly manage
connections. Pydantic AI can also open and close registered toolsets during
runs. Keep credentials on the backend. Resources are application-driven: a
client may read a profile explicitly and pass it as context; registering an
MCP toolset does not automatically turn every resource into model context.
See [`market_agent.py`](../examples/market_agent.py) and the
[Pydantic AI MCP client guide](https://ai.pydantic.dev/mcp/client/).

## AG-UI streams the coordinator

The React chat posts AG-UI requests to `/ag-ui`. `AGUIAdapter` runs the Pydantic
AI coordinator and streams protocol events to the browser. The UI reads tool
call events to show progress in the delegation trace.

## A2A delegates to specialists

The coordinator has tools that call the Company Fundamentals, Price Analyst,
and Market News specialist endpoints. Those agents expose A2A agent cards and
receive JSON-RPC messages. A2A is useful here because each specialist is a
separate agent endpoint with its own capability and task lifecycle; MCP remains
the interface the market agents use for data and operations.

## How the pieces fit

```text
User → React → AG-UI → Market Coordinator
                         ├─ MCP CodeMode for composed market operations
                         └─ A2A → specialist agent → MCP market server
```

The coordinator can choose among its available capabilities. Similar tasks may
be handled by different routes, so the chat trace is the source of truth for
which calls actually happened. The coordinator can use CodeMode without
delegating to the Price Analyst, or combine a specialist response with MCP
results when useful.

Implementation: [`a2a_web.py`](../src/experiment_mcp/agentic/a2a_web.py),
[`a2a_demo.py`](../src/experiment_mcp/a2a_demo.py), and
[`A2ADemo.tsx`](../ui/src/A2ADemo.tsx).

References: [Pydantic AI MCP client](https://ai.pydantic.dev/mcp/client/),
[FastMCP](https://gofastmcp.com/), and the
[A2A project](https://a2a-protocol.org/).
