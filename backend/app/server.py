"""FastAPI server — Andy Voice Agent.

Endpoints:
  POST /api/call        — Initiate outbound Twilio call to user
  GET/POST /twiml      — Return TwiML that routes call to OpenAI SIP
  POST /openai/webhook  — Handle OpenAI realtime.call.incoming event
  GET  /health          — Health check
  /*                    — Serve Next.js static frontend (if built)
"""

from __future__ import annotations

import asyncio
import logging
import os
from functools import partial

import websockets
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from openai import APIStatusError, AsyncOpenAI, InvalidWebhookSignatureError
from pydantic import BaseModel
from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import Dial, VoiceResponse

from agents.realtime.config import RealtimeSessionModelSettings
from agents.realtime.items import (
    AssistantAudio,
    AssistantMessageItem,
    AssistantText,
    InputText,
    UserMessageItem,
)
from agents.realtime.model_inputs import RealtimeModelSendRawMessage
from agents.realtime.openai_realtime import OpenAIRealtimeSIPModel
from agents.realtime.runner import RealtimeRunner

from .andy import WELCOME_MESSAGE, get_starting_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("andy_voice")


def _get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


OPENAI_API_KEY = _get_env("OPENAI_API_KEY")
OPENAI_WEBHOOK_SECRET = _get_env("OPENAI_WEBHOOK_SECRET")
OPENAI_PROJECT_ID = _get_env("OPENAI_PROJECT_ID")
TWILIO_ACCOUNT_SID = _get_env("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = _get_env("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = _get_env("TWILIO_PHONE_NUMBER")
BASE_URL = _get_env("BASE_URL")

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, webhook_secret=OPENAI_WEBHOOK_SECRET)
twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
andy = get_starting_agent()

app = FastAPI(title="Andy Voice Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track active call tasks to avoid duplicate observers
active_call_tasks: dict[str, asyncio.Task[None]] = {}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class CallRequest(BaseModel):
    phone_number: str


# ---------------------------------------------------------------------------
# Core call logic
# ---------------------------------------------------------------------------

async def accept_call(call_id: str) -> None:
    """Accept the incoming SIP call via OpenAI Realtime API."""
    instructions = (
        andy.instructions
        if isinstance(andy.instructions, str)
        else "You are Andy, a helpful AI employee."
    )
    try:
        await openai_client.post(
            f"/realtime/calls/{call_id}/accept",
            body={
                "type": "realtime",
                "model": "gpt-realtime-1.5",
                "instructions": instructions,
                "voice": "nova",
            },
            cast_to=dict,
        )
        logger.info("Accepted call %s", call_id)
    except APIStatusError as exc:
        if exc.status_code == 404:
            logger.warning("Call %s no longer exists (404). Skipping.", call_id)
            return
        logger.error("Failed to accept call %s: %s", call_id, exc.status_code)
        raise HTTPException(status_code=500, detail="Failed to accept call") from exc


async def observe_call(call_id: str) -> None:
    """Attach to realtime session, trigger greeting, log transcripts."""
    runner = RealtimeRunner(andy, model=OpenAIRealtimeSIPModel())
    initial_settings: RealtimeSessionModelSettings = {
        "turn_detection": {
            "type": "semantic_vad",
            "interrupt_response": True,
        }
    }
    try:
        async with await runner.run(
            model_config={
                "call_id": call_id,
                "initial_model_settings": initial_settings,
            }
        ) as session:
            # Trigger greeting immediately so caller doesn't hear silence
            await session.model.send_event(
                RealtimeModelSendRawMessage(
                    message={
                        "type": "response.create",
                        "other_data": {
                            "response": {
                                "instructions": (
                                    f"Say exactly '{WELCOME_MESSAGE}' now, "
                                    "then continue the conversation."
                                )
                            }
                        },
                    }
                )
            )

            async for event in session:
                if event.type == "history_added":
                    item = event.item
                    if isinstance(item, UserMessageItem):
                        for content in item.content:
                            if isinstance(content, InputText) and content.text:
                                logger.info("Caller: %s", content.text)
                    elif isinstance(item, AssistantMessageItem):
                        for content in item.content:
                            if isinstance(content, AssistantText) and content.text:
                                logger.info("Andy (text): %s", content.text)
                            elif isinstance(content, AssistantAudio) and content.transcript:
                                logger.info("Andy (audio): %s", content.transcript)
                elif event.type == "error":
                    logger.error("Realtime error: %s", event.error)

    except websockets.exceptions.ConnectionClosedError:
        logger.info("Call %s ended (WebSocket closed)", call_id)
    except Exception as exc:
        logger.exception("Error observing call %s", call_id, exc_info=exc)
    finally:
        active_call_tasks.pop(call_id, None)
        logger.info("Call %s cleaned up", call_id)


def _track_call_task(call_id: str) -> None:
    """Spawn observer task, skip if already running (handles webhook retries)."""
    existing = active_call_tasks.get(call_id)
    if existing and not existing.done():
        logger.info("Call %s already has an observer. Ignoring duplicate.", call_id)
        return
    active_call_tasks.pop(call_id, None)
    task = asyncio.create_task(observe_call(call_id))
    active_call_tasks[call_id] = task


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/call")
async def initiate_call(req: CallRequest) -> dict:
    """Initiate an outbound Twilio call to the user's phone number."""
    phone = req.phone_number.strip()
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number is required.")
    if not phone.startswith("+"):
        raise HTTPException(
            status_code=400,
            detail="Phone number must include country code (e.g. +1 555 123 4567).",
        )

    twiml_url = f"{BASE_URL}/twiml"
    try:
        call = await asyncio.get_event_loop().run_in_executor(
            None,
            partial(
                twilio_client.calls.create,
                to=phone,
                from_=TWILIO_PHONE_NUMBER,
                url=twiml_url,
            ),
        )
        logger.info("Outbound call initiated: %s → %s", call.sid, phone)
        return {"success": True, "call_sid": call.sid}
    except Exception as exc:
        logger.error("Twilio call failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.api_route("/twiml", methods=["GET", "POST"])
async def twiml_response() -> Response:
    """Return TwiML that routes the answered call to OpenAI SIP."""
    sip_uri = f"sip:proj_{OPENAI_PROJECT_ID}@sip.api.openai.com;transport=tls"
    response = VoiceResponse()
    dial = Dial()
    dial.sip(sip_uri)
    response.append(dial)
    return Response(content=str(response), media_type="application/xml")


@app.post("/openai/webhook")
async def openai_webhook(request: Request) -> Response:
    """Handle OpenAI webhook when a SIP call arrives."""
    body = await request.body()
    try:
        event = openai_client.webhooks.unwrap(body, request.headers)
    except InvalidWebhookSignatureError as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook signature") from exc

    if event.type == "realtime.call.incoming":
        call_id = event.data.call_id
        await accept_call(call_id)
        _track_call_task(call_id)

    return Response(status_code=200)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Serve Next.js static frontend (catch-all — MUST be last)
# ---------------------------------------------------------------------------

if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
