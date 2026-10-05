"""AG-UI coordinator and A2A specialist endpoints for the browser demo."""

import os

from a2a.client import ClientConfig, ClientFactory
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Message,
    Part,
    Role,
    SendMessageRequest,
)
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.ui.ag_ui import AGUIAdapter
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from experiment_mcp.a2a_demo import MarketSpecialistExecutor

MODEL_NAME = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")
SPECIALISTS = {
    "fundamentals": ("Company Fundamentals", "Company profile, sector and business overview."),
    "prices": ("Price Analyst", "Historical market prices and recent performance."),
    "news": ("Market News", "Recent news headlines associated with a ticker."),
}


def _agent_card(name: str, description: str, url: str, skill_id: str) -> AgentCard:
    return AgentCard(
        name=name,
        description=description,
        supported_interfaces=[
            AgentInterface(url=url, protocol_binding="JSONRPC", protocol_version="1.0")
        ],
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[AgentSkill(id=skill_id, name=name, description=description, tags=[skill_id])],
    )


def _text_from_response(response: object) -> str:
    kind = response.WhichOneof("payload")
    payload = getattr(response, kind) if kind else None
    if kind == "artifact_update":
        text = [part.text for part in payload.artifact.parts if part.text]
        if text:
            return "\n".join(text)
    if kind in {"message", "task"}:
        value = payload
        for artifact in getattr(value, "artifacts", []):
            text = [part.text for part in artifact.parts if part.text]
            if text:
                return "\n".join(text)
        message = getattr(value, "status", None)
        if message:
            text = [part.text for part in getattr(message, "message", Message()).parts if part.text]
            if text:
                return "\n".join(text)
        parts = getattr(value, "parts", [])
        text = [part.text for part in parts if part.text]
        if text:
            return "\n".join(text)
    if kind == "status_update":
        message = payload.status.message
        if message.parts:
            return "\n".join(part.text for part in message.parts if part.text)
    return "The agent finished without returning text."


async def _ask_specialist(base_url: str, user_request: str) -> str:
    client = await ClientFactory(ClientConfig(streaming=True)).create_from_url(base_url)
    request = SendMessageRequest(
        message=Message(
            message_id=os.urandom(16).hex(),
            role=Role.ROLE_USER,
            parts=[Part(text=user_request)],
        )
    )
    chunks = []
    async with client:
        async for response in client.send_message(request):
            chunks.append(_text_from_response(response))
    return next(
        (
            chunk
            for chunk in reversed(chunks)
            if chunk != "The agent finished without returning text."
        ),
        chunks[-1] if chunks else "No response from the specialist.",
    )


def create_coordinator(
    api_key: str,
    a2a_base_url: str,
    code_mode_mcp_url: str,
    mcp_token: str,
) -> Agent[None, str]:
    model = OpenRouterModel(MODEL_NAME, provider=OpenRouterProvider(api_key=api_key))
    code_mode = MCPToolset(code_mode_mcp_url, auth=mcp_token)
    agent = Agent(
        model,
        name="market_coordinator",
        toolsets=[code_mode],
        instructions=(
            "You coordinate a market research team and synthesize market evidence returned "
            "by your colleagues. Do not provide investment advice. Never expose private reasoning."
        ),
    )

    @agent.tool
    async def delegate_to_fundamentals_agent(
        ctx: RunContext[None], ticker: str, request: str
    ) -> str:
        """Ask the Company Fundamentals agent for profile and business context."""
        del ctx
        return await _ask_specialist(f"{a2a_base_url}/fundamentals", f"Ticker {ticker}. {request}")

    @agent.tool
    async def delegate_to_price_analyst(ctx: RunContext[None], ticker: str, request: str) -> str:
        """Ask the Price Analyst agent for recent historical prices and performance."""
        del ctx
        return await _ask_specialist(f"{a2a_base_url}/prices", f"Ticker {ticker}. {request}")

    @agent.tool
    async def delegate_to_market_news(ctx: RunContext[None], ticker: str, request: str) -> str:
        """Ask the Market News agent for recent news headlines about a ticker."""
        del ctx
        return await _ask_specialist(f"{a2a_base_url}/news", f"Ticker {ticker}. {request}")

    return agent


async def ag_ui(request: Request) -> Response:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return JSONResponse(
            {"error": "Set OPENROUTER_API_KEY in .env to use the chat."}, status_code=503
        )
    base_url = os.getenv("A2A_PUBLIC_URL", "http://127.0.0.1:8100")
    code_mode_url = os.getenv("CODE_MODE_MCP_URL", "http://127.0.0.1:8001/mcp")
    mcp_token = os.getenv("MCP_DEV_TOKEN", "")
    agent = create_coordinator(api_key, base_url, code_mode_url, mcp_token)
    return await AGUIAdapter.dispatch_request(request, agent=agent)


def create_app() -> Starlette:
    mcp_url = os.getenv("MCP_URL", "http://mcp-server:8000/mcp")
    token = os.getenv("MCP_DEV_TOKEN", "")
    routes = [Route("/ag-ui", ag_ui, methods=["POST"])]
    for key, (name, description) in SPECIALISTS.items():
        path = f"/{key}"
        card = _agent_card(
            name, description, f"{os.getenv('A2A_PUBLIC_URL', 'http://127.0.0.1:8100')}{path}", key
        )
        handler = DefaultRequestHandler(
            agent_executor=MarketSpecialistExecutor(key, mcp_url, token),
            task_store=InMemoryTaskStore(),
            agent_card=card,
        )
        routes.extend(create_jsonrpc_routes(handler, rpc_url=path))
        routes.extend(
            create_agent_card_routes(card, card_url=f"{path}/.well-known/agent-card.json")
        )
    return Starlette(routes=routes)


app = create_app()
