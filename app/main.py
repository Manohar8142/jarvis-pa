"""Jarvis PA - FastAPI gateway."""
from fastapi import FastAPI

from app.voice.twilio_routes import router as voice_router

app = FastAPI(title="Jarvis PA", version="0.1.0")
app.include_router(voice_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
