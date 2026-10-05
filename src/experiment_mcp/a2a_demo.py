"""A2A specialist agents used by the AG-UI delegation demo."""

import json
import re
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Message, Part, Role, Task, TaskState, TaskStatus
from fastmcp import Client


class MarketSpecialistExecutor(AgentExecutor):
    """Fetch one focused slice of market context from the MCP server."""

    def __init__(self, kind: str, mcp_url: str, token: str) -> None:
        self.kind = kind
        self.mcp_url = mcp_url
        self.token = token

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id or str(uuid4())
        context_id = context.context_id or task_id
        await event_queue.enqueue_event(
            Task(
                id=task_id,
                context_id=context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED),
            )
        )
        updater = TaskUpdater(event_queue, task_id=task_id, context_id=context_id)
        await updater.submit()
        await updater.start_work()
        try:
            prompt = context.get_user_input()
            ticker_match = re.search(
                r"\bticker\s+([A-Za-z][A-Za-z0-9.-]{0,9})\b", prompt, re.IGNORECASE
            )
            ticker = ticker_match.group(1).upper() if ticker_match else "AAPL"
            async with Client(self.mcp_url, auth=self.token) as mcp:
                if self.kind == "fundamentals":
                    data = await mcp.read_resource(f"market://symbols/{ticker}")
                    answer = f"Company profile for {ticker}: {_as_text(data)}"
                elif self.kind == "prices":
                    result = await mcp.call_tool(
                        "get_price_history", {"ticker": ticker, "period": "1mo", "interval": "1d"}
                    )
                    answer = f"Recent price history for {ticker}: {_as_text(result)}"
                else:
                    data = await mcp.read_resource(f"market://symbols/{ticker}/news")
                    answer = f"Recent news for {ticker}: {_as_text(data)}"
            await updater.add_artifact([Part(text=answer, media_type="text/plain")])
            await updater.complete()
        except Exception:
            await updater.failed(
                Message(
                    role=Role.ROLE_AGENT,
                    parts=[Part(text="Could not retrieve data from the MCP server.")],
                )
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        del context, event_queue


def _as_text(value: object) -> str:
    content = getattr(value, "content", None) or getattr(value, "contents", None)
    if content is None and isinstance(value, list):
        content = value
    if content:
        texts = [item.text for item in content if getattr(item, "text", None)]
        if texts:
            return "\n".join(texts)
    if hasattr(value, "model_dump"):
        return json.dumps(value.model_dump(mode="json"), ensure_ascii=False, default=str)
    return json.dumps(value, ensure_ascii=False, default=str)
