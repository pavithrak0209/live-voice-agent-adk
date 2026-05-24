"""
Live multi-agent voice system using Google ADK + Gemini Live.

Run:
    python main.py

Speak into your microphone. Press Ctrl+C to stop.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

from google.adk.runners import Runner, RunConfig
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.sessions import InMemorySessionService
from google.genai.types import (
    SpeechConfig,
    VoiceConfig,
    PrebuiltVoiceConfig,
    Blob,
)

from agents import root_agent
from voice_io import AudioIO, SAMPLE_RATE, CHUNK_SIZE

APP_NAME = "voice_agent_app"
USER_ID = "user_001"
SESSION_ID = "session_001"


async def run_voice_session():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not set in .env")
        sys.exit(1)

    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    run_config = RunConfig(
        response_modalities=["AUDIO"],
        speech_config=SpeechConfig(
            voice_config=VoiceConfig(
                prebuilt_voice_config=PrebuiltVoiceConfig(voice_name="Puck")
            )
        ),
    )

    live_queue = LiveRequestQueue()
    audio = AudioIO()
    audio.open_input()
    audio.open_output()

    print("\n=== Voice Agent Ready ===")
    print("Speak into your microphone. Press Ctrl+C to stop.\n")

    async def send_audio():
        """Read mic chunks and push them into the live request queue."""
        loop = asyncio.get_event_loop()
        try:
            while True:
                chunk = await loop.run_in_executor(None, audio.read_chunk)
                live_queue.send_realtime(
                    Blob(data=chunk, mime_type=f"audio/pcm;rate={SAMPLE_RATE}")
                )
        except asyncio.CancelledError:
            live_queue.close()

    async def receive_events():
        """Consume events from run_live and play audio parts."""
        async for event in runner.run_live(
            user_id=USER_ID,
            session_id=SESSION_ID,
            live_request_queue=live_queue,
            run_config=run_config,
        ):
            # Play audio chunks as they arrive
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.inline_data and part.inline_data.mime_type.startswith("audio"):
                        audio.write_chunk(part.inline_data.data)

            # Print transcriptions so you can follow along
            if event.output_transcription and event.output_transcription.text:
                print(f"Agent: {event.output_transcription.text}", end="", flush=True)
            if event.input_transcription and event.input_transcription.text:
                print(f"\nYou:   {event.input_transcription.text}", flush=True)

    sender = asyncio.create_task(send_audio())
    try:
        await receive_events()
    except KeyboardInterrupt:
        pass
    finally:
        sender.cancel()
        await asyncio.gather(sender, return_exceptions=True)
        audio.close()
        print("\nSession ended.")


if __name__ == "__main__":
    asyncio.run(run_voice_session())
