"""Tests for the POST /api/call endpoint."""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.asyncio
async def test_call_requires_phone_number(client):
    response = await client.post("/api/call", json={})
    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_call_rejects_empty_phone(client):
    response = await client.post("/api/call", json={"phone_number": ""})
    assert response.status_code == 400
    assert "required" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_call_rejects_missing_country_code(client):
    response = await client.post("/api/call", json={"phone_number": "03001234567"})
    assert response.status_code == 400
    assert "country code" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_call_initiates_with_valid_number(client):
    mock_call = MagicMock()
    mock_call.sid = "CA1234567890"

    with patch("backend.app.server.twilio_client") as mock_twilio:
        mock_twilio.calls.create.return_value = mock_call
        response = await client.post("/api/call", json={"phone_number": "+923001234567"})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["call_sid"] == "CA1234567890"


@pytest.mark.asyncio
async def test_call_handles_twilio_error(client):
    with patch("backend.app.server.twilio_client") as mock_twilio:
        mock_twilio.calls.create.side_effect = Exception("Twilio error: invalid number")
        response = await client.post("/api/call", json={"phone_number": "+923001234567"})

    assert response.status_code == 500
