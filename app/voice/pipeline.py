"""Pipecat pipeline over Twilio Media Streams.

Twilio audio -> Silero VAD + Smart Turn -> Deepgram STT -> Groq LLM -> ElevenLabs TTS -> Twilio.
Pipecat's API moves fast; pin the version in requirements.txt and check
https://docs.pipecat.ai/guides/telephony/twilio-websockets if an import changes.
"""
import json

from fastapi import WebSocket

from app.config import settings
from app.voice.prompts import system_prompt


async def _read_start(websocket: WebSocket) -> tuple[str, str, str]:
    """Twilio sends 'connected' then 'start' with streamSid, callSid and custom parameters."""
    stream_sid = call_sid = ""
    purpose = "brief"
    async for raw in websocket.iter_text():
        msg = json.loads(raw)
        if msg.get("event") == "start":
            start = msg["start"]
            stream_sid, call_sid = start["streamSid"], start["callSid"]
            purpose = start.get("customParameters", {}).get("purpose", "brief")
            break
    return stream_sid, call_sid, purpose


async def run_call(websocket: WebSocket) -> None:
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineParams, PipelineTask
    from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
    from pipecat.serializers.twilio import TwilioFrameSerializer
    from pipecat.services.deepgram.stt import DeepgramSTTService
    from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
    from pipecat.services.groq.llm import GroqLLMService
    from pipecat.transports.network.fastapi_websocket import (
        FastAPIWebsocketParams,
        FastAPIWebsocketTransport,
    )

    stream_sid, call_sid, purpose = await _read_start(websocket)

    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_analyzer=SileroVADAnalyzer(),
            serializer=TwilioFrameSerializer(
                stream_sid=stream_sid,
                call_sid=call_sid,
                account_sid=settings.twilio_account_sid,
                auth_token=settings.twilio_auth_token,
            ),
        ),
    )

    stt = DeepgramSTTService(api_key=settings.deepgram_api_key)
    llm = GroqLLMService(api_key=settings.groq_api_key, model="llama-3.3-70b-versatile")
    tts = ElevenLabsTTSService(
        api_key=settings.elevenlabs_api_key,
        voice_id=settings.elevenlabs_voice_id,
        model="eleven_flash_v2_5",
    )

    context = OpenAILLMContext([{"role": "system", "content": system_prompt(purpose)}])
    agg = llm.create_context_aggregator(context)

    pipeline = Pipeline(
        [transport.input(), stt, agg.user(), llm, tts, transport.output(), agg.assistant()]
    )
    task = PipelineTask(
        pipeline,
        params=PipelineParams(audio_in_sample_rate=8000, audio_out_sample_rate=8000, allow_interruptions=True),
    )

    @transport.event_handler("on_client_connected")
    async def _greet(_transport, _client):
        await task.queue_frames([agg.user().get_context_frame()])

    await PipelineRunner(handle_sigint=False).run(task)
