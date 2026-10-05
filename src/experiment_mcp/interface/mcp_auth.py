"""Local bearer-token authentication for the learning server."""

from fastmcp.server.auth.providers.jwt import StaticTokenVerifier


def create_local_auth(token: str | None) -> StaticTokenVerifier:
    """Create a single-scope development token verifier."""
    if not token:
        raise RuntimeError("Define MCP_DEV_TOKEN in the environment or project .env file.")
    if len(token) < 32:
        raise ValueError("MCP_DEV_TOKEN must contain at least 32 characters.")

    return StaticTokenVerifier(
        tokens={
            token: {
                "client_id": "quantinsider-local-client",
                "scopes": ["market:read"],
            }
        },
        required_scopes=["market:read"],
    )
