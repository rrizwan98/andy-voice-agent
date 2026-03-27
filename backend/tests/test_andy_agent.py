"""Tests for Andy agent definition."""

import pytest


def test_andy_agent_exists():
    from backend.app.andy import andy_agent
    assert andy_agent is not None


def test_andy_agent_name():
    from backend.app.andy import andy_agent
    assert andy_agent.name == "Andy"


def test_andy_has_instructions():
    from backend.app.andy import andy_agent
    assert andy_agent.instructions
    assert len(andy_agent.instructions) > 100


def test_welcome_message_mentions_whatsapp():
    from backend.app.andy import WELCOME_MESSAGE
    assert "WhatsApp" in WELCOME_MESSAGE or "whatsapp" in WELCOME_MESSAGE.lower()


def test_welcome_message_mentions_24_7():
    from backend.app.andy import WELCOME_MESSAGE
    assert "24/7" in WELCOME_MESSAGE


def test_get_starting_agent_returns_andy():
    from backend.app.andy import get_starting_agent, andy_agent
    agent = get_starting_agent()
    assert agent is andy_agent


def test_andy_instructions_mention_builds():
    from backend.app.andy import andy_agent
    instructions = andy_agent.instructions.lower()
    assert "website" in instructions or "build" in instructions
