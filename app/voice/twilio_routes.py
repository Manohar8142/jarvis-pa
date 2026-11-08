"""Twilio call entry points.

POST /voice/incoming  -> TwiML that opens a Media Stream to /voice/ws
POST /voice/call-me   -> places an outbound call to the owner (morning brief / reminder)
WS   /voice/ws        -> bidirectional audio, handed to the Pipecat pipeline
"""
from fastapi import APIRouter, Request, WebSocket
from fastapi.responses import Response

from app.config import settings

router = APIRouter(prefix="/voice", tags=["voice"])


def _stream_twiml(purpose: str) -> str:
    ws_url = settings.public_base_url.replace("https://", "wss://").replace("http://", "ws://")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response><Connect>"
        f'<Stream url="{ws_url}/voice/ws">'
        f'<Parameter name="purpose" value="{purpose}"/>'
        "</Stream></Connect></Response>"
    )


@router.post("/incoming")
async def incoming(request: Request) -> Response:
    """Inbound call (screening). Twilio number's voice webhook points here."""
    return Response(_stream_twiml("screen"), media_type="application/xml")


@router.post("/outbound-twiml")
async def outbound_twiml(purpose: str = "brief") -> Response:
    return Response(_stream_twiml(purpose), media_type="application/xml")


@router.post("/call-me")
async def call_me(purpose: str = "brief") -> dict:
    """Ring the owner's phone. purpose: brief | reminder."""
    from twilio.rest import Client

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    call = client.calls.create(
        to=settings.owner_phone,
        from_=settings.twilio_phone_number,
        url=f"{settings.public_base_url}/voice/outbound-twiml?purpose={purpose}",
    )
    return {"call_sid": call.sid}


@router.websocket("/ws")
async def media_ws(websocket: WebSocket) -> None:
    from app.voice.pipeline import run_call

    await websocket.accept()
    await run_call(websocket)
