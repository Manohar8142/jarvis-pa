# Jarvis PA

Personal voice assistant: morning brief calls, talk-back reminders, call screening, research on WhatsApp.

## Run
```bash
cp .env.example .env   # fill keys
docker build -t jarvis-pa . && docker run --env-file .env -p 8000:8000 jarvis-pa
curl localhost:8000/health   # {"status":"ok"}
```

## Voice call (dev)
1. `ngrok http 8000`, put the URL in `PUBLIC_BASE_URL`.
2. Point your Twilio number's Voice webhook to `POST {PUBLIC_BASE_URL}/voice/incoming` (screening).
3. `curl -X POST "localhost:8000/voice/call-me?purpose=brief"` rings your phone.

Pipeline: Twilio Media Streams -> Silero VAD -> Deepgram STT -> Groq LLM -> ElevenLabs Flash TTS (Pipecat).
