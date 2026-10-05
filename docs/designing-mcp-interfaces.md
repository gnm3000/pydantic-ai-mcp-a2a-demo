# Designing MCP Interfaces

Choose an MCP primitive based on the interaction a client needs, not on whether
the underlying backend endpoint uses HTTP `GET` or `POST`.

| Primitive | Use it when the client needs… | MarketInsider example |
| --- | --- | --- |
| Tool | An operation the model can invoke with validated arguments | `get_price_history`, `summarize_prices` |
| Resource | Addressable information a host can read and add to context | `market://symbols/NVDA` |
| Resource template | A family of addressable resources selected by URI parameters | `market://symbols/{ticker}/quote` |
| Prompt | A reusable, named message template the user or host can select | `analyze_ticker` |

Resources are application-driven: the host decides when to read them and how
to provide their contents to a model. A resource is not automatically a tool
call. A GET endpoint can still make sense as a tool when the model should
choose when to call it and provide arguments; a resource is useful when clients
benefit from a stable URI for reading a piece of context.

## Tools: expose operations

Use tools for calculations, searches, lookups initiated by the model, or
operations with a meaningful action. Give tools precise names, typed inputs,
and descriptions that explain the result. FastMCP derives the input schema from
the Python signature. This project registers its operations in
[`mcp_tools.py`](../src/experiment_mcp/interface/mcp_tools.py).

```python
@mcp.tool
def summarize_prices(prices: list[float]) -> dict[str, float | int]:
    """Return the count, minimum, maximum, and average closing price."""
    return summarize_price_values(prices)
```

Tools should validate inputs, return data in a form clients can use, and avoid
surprising side effects. Mark read-only or destructive behavior with accurate
annotations when applicable.

## Resources: expose readable context

Use resources for content that has a useful identity and can be read
independently of a tool action. MarketInsider uses resource templates for
ticker profiles, quotes, recommendations, calendars, news, and corporate
actions. See [`mcp_resources.py`](../src/experiment_mcp/interface/mcp_resources.py).

```python
@mcp.resource("market://symbols/{ticker}", mime_type="application/json")
async def read_ticker_info(ctx: Context, ticker: str) -> dict[str, object]:
    """Read company profile and classification data for one ticker."""
    ...
```

Use a URI template when the client should request different resources by
substituting a URI parameter. FastMCP screens templated-resource parameters for
path traversal by default, but handlers that join values to filesystem paths
must still anchor the final path under an allowed root.

## Prompts: expose reusable workflows

Use prompts when users or hosts should select a reusable message template with
arguments. Prompts can be versioned; this server exposes two versions of
`analyze_ticker` in [`mcp_prompts.py`](../src/experiment_mcp/interface/mcp_prompts.py).
The prompt packages a request and context references. The client still decides
how to fetch and supply resource content.

## Quick decision

- “Calculate a comparison when asked” → tool.
- “Read this profile at a known ticker URI” → resource template.
- “Start from a reusable ticker-analysis template” → prompt.
- “Combine price history, comparison, and trend calculations” → a CodeMode
  workflow over tools; see [CodeMode](code-mode.md).

Official references: [FastMCP tools](https://gofastmcp.com/servers/tools),
[resources](https://gofastmcp.com/servers/resources), and
[prompts](https://gofastmcp.com/servers/prompts).
