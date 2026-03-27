"""Tests for the /twiml endpoint."""

import pytest


@pytest.mark.asyncio
async def test_twiml_returns_xml(client):
    response = await client.get("/twiml")
    assert response.status_code == 200
    assert "xml" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_twiml_contains_dial(client):
    response = await client.get("/twiml")
    assert "<Dial>" in response.text or "<Dial " in response.text


@pytest.mark.asyncio
async def test_twiml_contains_openai_sip(client):
    response = await client.get("/twiml")
    assert "sip.api.openai.com" in response.text


@pytest.mark.asyncio
async def test_twiml_contains_project_id(client):
    response = await client.get("/twiml")
    assert "proj_test123456" in response.text


@pytest.mark.asyncio
async def test_twiml_post_also_works(client):
    response = await client.post("/twiml")
    assert response.status_code == 200
    assert "sip.api.openai.com" in response.text
