---
title: Andy Voice Agent Backend
emoji: 🤖
colorFrom: indigo
colorTo: blue
sdk: docker
pinned: false
app_port: 7860
---

# Andy Voice Agent — Backend

FastAPI backend for Andy Voice Agent powered by OpenAI Realtime API.

## Endpoints

- `POST /api/call` — Initiate outbound Twilio call
- `GET/POST /twiml` — TwiML for call routing
- `POST /openai/webhook` — OpenAI realtime webhook
- `GET /health` — Health check
