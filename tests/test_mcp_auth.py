"""Tests for the local bearer-token verifier."""

import asyncio

import pytest

from experiment_mcp.interface.mcp_auth import create_local_auth


def test_local_auth_accepts_the_configured_token_with_read_scope():
    verifier = create_local_auth("local-test-token-0123456789abcdef")

    access_token = asyncio.run(verifier.verify_token("local-test-token-0123456789abcdef"))

    assert access_token is not None
    assert access_token.client_id == "quantinsider-local-client"
    assert access_token.scopes == ["market:read"]


def test_local_auth_rejects_unknown_tokens():
    verifier = create_local_auth("local-test-token-0123456789abcdef")

    assert asyncio.run(verifier.verify_token("wrong-token")) is None


@pytest.mark.parametrize("token", [None, ""])
def test_local_auth_requires_a_token(token):
    with pytest.raises(RuntimeError, match="MCP_DEV_TOKEN"):
        create_local_auth(token)


def test_local_auth_rejects_a_weak_token():
    with pytest.raises(ValueError, match="32 characters"):
        create_local_auth("adminadmin")
