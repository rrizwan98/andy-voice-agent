"""Tests for the POST /openai/webhook endpoint."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


@pytest.mark.asyncio
async def test_webhook_rejects_invalid_signature(client):
    response = await client.post(
        "/openai/webhook",
        content=b'{"type": "realtime.call.incoming"}',
        headers={"content-type": "application/json"},
    )
    # Should return 400 for invalid signature
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_webhook_accepts_valid_event(client):
    mock_event = MagicMock()
    mock_event.type = "realtime.call.incoming"
    mock_event.data.call_id = "call_test123"

    with patch("backend.app.server.openai_client") as mock_openai:
        mock_openai.webhooks.unwrap.return_value = mock_event
        mock_openai.post = AsyncMock(return_value={})

        with patch("backend.app.server._track_call_task"):
            with patch("backend.app.server.accept_call", new_callable=AsyncMock):
                response = await client.post(
                    "/openai/webhook",
                    content=b"{}",
                    headers={"content-type": "application/json"},
                )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook_handles_unknown_event_type(client):
    mock_event = MagicMock()
    mock_event.type = "some.unknown.event"

    with patch("backend.app.server.openai_client") as mock_openai:
        mock_openai.webhooks.unwrap.return_value = mock_event
        response = await client.post(
            "/openai/webhook",
            content=b"{}",
            headers={"content-type": "application/json"},
        )

    assert response.status_code == 200
