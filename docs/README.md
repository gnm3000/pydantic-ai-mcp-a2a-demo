# MCP Builder's Guide

This guide uses the MarketInsider repository as a working example of an MCP
server and its agent clients. It is written for developers and coding agents
that need to design, implement, or review MCP capabilities.

## Suggested reading paths

### Build a server

1. [Repository architecture](architecture.md)
2. [Choose tools, resources, or prompts](designing-mcp-interfaces.md)
3. [Build and run a FastMCP server](building-a-fastmcp-server.md)
4. [Test the server and CI](testing-and-ci.md)

### Connect an agent

1. [Architecture](architecture.md)
2. [Pydantic AI, AG-UI, and A2A](agents-and-a2a.md)
3. [CodeMode](code-mode.md), when an agent needs to compose several MCP calls

## Guides

- [Architecture](architecture.md): request flows, package layout, and service
  boundaries.
- [Designing MCP interfaces](designing-mcp-interfaces.md): how to decide what
  belongs in a tool, resource, resource template, or prompt.
- [Building a FastMCP server](building-a-fastmcp-server.md): project setup,
  typed components, composition, security, and local execution.
- [Testing and CI](testing-and-ci.md): fast deterministic tests, coverage,
  frontend checks, and current automation limits.
- [Agents and A2A](agents-and-a2a.md): consume an MCP server from Pydantic AI
  and understand the coordinator/specialist demo.
- [CodeMode](code-mode.md): sandboxed tool composition, tradeoffs, and the
  implementation in this repository.

## How to use these docs

The guides describe this repository's implementation and link to the code that
demonstrates each pattern. They are not a substitute for the MCP specification
or the official framework references. FastMCP APIs evolve; check the
[FastMCP documentation](https://gofastmcp.com/) and the resolved dependency in
`uv.lock` before copying an API into another project.

For project-specific instructions intended for coding agents, see the root
[`AGENTS.md`](../AGENTS.md). If a guide and the implementation disagree, verify
the code and tests, then update the guide in the same change.
