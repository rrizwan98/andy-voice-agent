"""Test configuration — sets env vars before any app imports."""

import os

import pytest
from httpx import ASGITransport, AsyncClient

# Set required env vars before importing the app
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-for-testing")
os.environ.setdefault("OPENAI_WEBHOOK_SECRET", "whsec_test_secret_for_testing")
os.environ.setdefault("OPENAI_PROJECT_ID", "proj_test123456")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "ACtest1234567890123456789012345678")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test_auth_token_1234567890123456")
os.environ.setdefault("TWILIO_PHONE_NUMBER", "+15005550006")
os.environ.setdefault("BASE_URL", "https://test-user-openai-first-voice-agent.hf.space")


@pytest.fixture
async def client():
    from backend.app.server import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
