# React MCP App and agent demo

This Vite application contains two demos:

- `/` is a price explorer that runs as an MCP App in an MCP Apps-compatible
  host.
- `/a2a` is an AG-UI chat that delegates research to A2A specialist agents.

From the repository root, install dependencies and start the development stack:

```bash
npm --prefix ui ci
npm --prefix ui run dev
```

The app expects a running MCP Apps host for the price explorer and the
`agent-web` service for the A2A chat. See the root README for the full Docker
Compose setup.
