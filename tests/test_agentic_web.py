"""Unit tests for the AG-UI and A2A web adapter helpers."""

import asyncio
from types import SimpleNamespace

import pytest
from starlette.requests import Request

from experiment_mcp.agentic import a2a_web


def _message(text: str) -> SimpleNamespace:
    return SimpleNamespace(parts=[SimpleNamespace(text=text)])


@pytest.mark.parametrize(
    ("kind", "payload", "expected"),
    [
        (
            "artifact_update",
            SimpleNamespace(artifact=SimpleNamespace(parts=[_message("from artifact").parts[0]])),
            "from artifact",
        ),
        (
            "message",
            SimpleNamespace(artifacts=[SimpleNamespace(parts=[_message("from message").parts[0]])]),
            "from message",
        ),
        (
            "task",
            SimpleNamespace(
                artifacts=[],
                status=SimpleNamespace(message=_message("from status")),
                parts=[],
            ),
            "from status",
        ),
        (
            "task",
            SimpleNamespace(artifacts=[], status=None, parts=[_message("from parts").parts[0]]),
            "from parts",
        ),
        (
            "status_update",
            SimpleNamespace(status=SimpleNamespace(message=_message("status event"))),
            "status event",
        ),
        (None, None, "The agent finished without returning text."),
    ],
)
def test_text_from_response_handles_a2a_payload_shapes(kind, payload, expected):
    response = SimpleNamespace(WhichOneof=lambda _field: kind)
    if kind:
        setattr(response, kind, payload)

    assert a2a_web._text_from_response(response) == expected


def test_ask_specialist_returns_latest_nonempty_response(monkeypatch):
    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def send_message(self, _request):
            yield SimpleNamespace(
                WhichOneof=lambda _field: "message",
                message=SimpleNamespace(parts=[SimpleNamespace(text="first")]),
            )
            yield SimpleNamespace(WhichOneof=lambda _field: None)

    class Factory:
        async def create_from_url(self, _url):
            return Client()

    monkeypatch.setattr(a2a_web, "ClientFactory", lambda _config: Factory())
    assert asyncio.run(a2a_web._ask_specialist("http://agent", "research NVDA")) == "first"


def test_ask_specialist_falls_back_when_agent_returns_no_chunks(monkeypatch):
    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def send_message(self, _request):
            if False:
                yield None

    class Factory:
        async def create_from_url(self, _url):
            return Client()

    monkeypatch.setattr(a2a_web, "ClientFactory", lambda _config: Factory())
    assert (
        asyncio.run(a2a_web._ask_specialist("http://agent", "research NVDA"))
        == "No response from the specialist."
    )


def test_ag_ui_requires_openrouter_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    response = asyncio.run(
        a2a_web.ag_ui(Request({"type": "http", "method": "POST", "path": "/ag-ui", "headers": []}))
    )

    assert response.status_code == 503


def test_ag_ui_dispatches_with_configured_model(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("A2A_PUBLIC_URL", "http://agents")
    monkeypatch.setenv("CODE_MODE_MCP_URL", "http://code-mode/mcp")
    monkeypatch.setenv("MCP_DEV_TOKEN", "test-token")
    monkeypatch.setattr(
        a2a_web,
        "create_coordinator",
        lambda key, url, code_url, token: (key, url, code_url, token),
    )

    async def dispatch(_request, *, agent):
        return SimpleNamespace(status_code=200, body=agent)

    monkeypatch.setattr(a2a_web.AGUIAdapter, "dispatch_request", dispatch)
    response = asyncio.run(
        a2a_web.ag_ui(Request({"type": "http", "method": "POST", "path": "/ag-ui", "headers": []}))
    )

    assert response.status_code == 200
    assert response.body == (
        "test-key",
        "http://agents",
        "http://code-mode/mcp",
        "test-token",
    )


def test_coordinator_delegates_to_each_specialist(monkeypatch):
    calls = []

    async def ask(url, text):
        calls.append((url, text))
        return "specialist result"

    monkeypatch.setattr(a2a_web, "_ask_specialist", ask)
    agent = a2a_web.create_coordinator(
        "test-key", "http://agents", "http://code-mode/mcp", "test-token"
    )
    tools = agent._function_toolset.tools

    async def invoke_all():
        return [
            await tools[name].function(None, "NVDA", "review the data")
            for name in (
                "delegate_to_fundamentals_agent",
                "delegate_to_price_analyst",
                "delegate_to_market_news",
            )
        ]

    assert asyncio.run(invoke_all()) == ["specialist result"] * 3
    assert calls == [
        ("http://agents/fundamentals", "Ticker NVDA. review the data"),
        ("http://agents/prices", "Ticker NVDA. review the data"),
        ("http://agents/news", "Ticker NVDA. review the data"),
    ]


def test_coordinator_connects_to_authenticated_code_mode_server():
    agent = a2a_web.create_coordinator(
        "test-key", "http://agents", "http://code-mode/mcp", "test-token"
    )

    toolset = agent._user_toolsets[0]
    assert toolset.client.transport.url == "http://code-mode/mcp"
    assert toolset.client.transport.auth is not None


def test_create_app_registers_ag_ui_and_three_specialist_endpoints(monkeypatch):
    monkeypatch.setenv("MCP_URL", "http://mcp/mcp")
    monkeypatch.setenv("MCP_DEV_TOKEN", "test-token")
    monkeypatch.setenv("A2A_PUBLIC_URL", "http://agents")

    app = a2a_web.create_app()

    assert {route.path for route in app.routes} >= {
        "/ag-ui",
        "/fundamentals",
        "/prices",
        "/news",
        "/fundamentals/.well-known/agent-card.json",
        "/prices/.well-known/agent-card.json",
        "/news/.well-known/agent-card.json",
    }
