"""Unit tests for A2A specialist task execution and payload serialization."""

import asyncio
from types import SimpleNamespace

import pytest

from experiment_mcp import a2a_demo


class EventQueue:
    def __init__(self) -> None:
        self.events = []

    async def enqueue_event(self, event) -> None:
        self.events.append(event)


class Updater:
    instances = []

    def __init__(self, *_args, **_kwargs) -> None:
        self.artifacts = []
        self.failure = None
        self.completed = False
        self.__class__.instances.append(self)

    async def submit(self):
        pass

    async def start_work(self):
        pass

    async def add_artifact(self, parts):
        self.artifacts.append(parts)

    async def complete(self):
        self.completed = True

    async def failed(self, message):
        self.failure = message


class MCPClient:
    def __init__(self, _url, *, auth):
        self.auth = auth

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def read_resource(self, uri):
        return [SimpleNamespace(text=f"read {uri}")]

    async def call_tool(self, name, arguments):
        return SimpleNamespace(
            content=[SimpleNamespace(text=f"called {name} {arguments['ticker']}")]
        )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ([SimpleNamespace(text="one"), SimpleNamespace(text="two")], "one\ntwo"),
        (SimpleNamespace(contents=[SimpleNamespace(text="wrapped")]), "wrapped"),
        (SimpleNamespace(model_dump=lambda **_kwargs: {"value": 1}), '{"value": 1}'),
        ({"value": 1}, '{"value": 1}'),
    ],
)
def test_as_text_formats_supported_result_shapes(value, expected):
    assert a2a_demo._as_text(value) == expected


@pytest.mark.parametrize(
    ("kind", "expected_fragment"),
    [
        ("fundamentals", "Company profile for NVDA"),
        ("prices", "Recent price history for NVDA"),
        ("news", "Recent news for NVDA"),
    ],
)
def test_specialist_fetches_requested_market_context(monkeypatch, kind, expected_fragment):
    Updater.instances.clear()
    monkeypatch.setattr(a2a_demo, "TaskUpdater", Updater)
    monkeypatch.setattr(a2a_demo, "Client", MCPClient)
    executor = a2a_demo.MarketSpecialistExecutor(kind, "http://mcp", "test-token")
    context = SimpleNamespace(
        task_id="task-1", context_id="context-1", get_user_input=lambda: "ticker nvda"
    )
    queue = EventQueue()

    asyncio.run(executor.execute(context, queue))

    assert queue.events
    updater = Updater.instances[-1]
    assert updater.completed
    assert expected_fragment in updater.artifacts[0][0].text


def test_specialist_uses_default_symbol_and_reports_upstream_failure(monkeypatch):
    Updater.instances.clear()
    monkeypatch.setattr(a2a_demo, "TaskUpdater", Updater)

    class BrokenClient(MCPClient):
        async def read_resource(self, _uri):
            raise RuntimeError("upstream failed")

    monkeypatch.setattr(a2a_demo, "Client", BrokenClient)
    executor = a2a_demo.MarketSpecialistExecutor("fundamentals", "http://mcp", "token")
    context = SimpleNamespace(
        task_id=None, context_id=None, get_user_input=lambda: "company overview"
    )
    queue = EventQueue()

    asyncio.run(executor.execute(context, queue))

    updater = Updater.instances[-1]
    assert not updater.completed
    assert "Could not retrieve data" in updater.failure.parts[0].text


def test_specialist_cancel_is_a_noop():
    executor = a2a_demo.MarketSpecialistExecutor("news", "http://mcp", "token")

    asyncio.run(executor.cancel(object(), object()))
