# Technical Reference — Live Multi-Agent Voice System

## Technology Stack

| Layer | Library / Service | Version | Purpose |
|---|---|---|---|
| Agent framework | `google-adk` | 2.1.0 | Agent definition, multi-agent routing, live runner |
| AI models | Gemini 2.0 Flash Live | cloud | Real-time voice I/O, ASR, TTS |
| AI models | Gemini 2.0 Flash | cloud | Sub-agent reasoning & tool calls |
| Genai SDK | `google-genai` | 1.75.0 | Low-level Gemini API types & client |
| Audio I/O | `pyaudio` | 0.2.14 | Microphone capture, speaker playback |
| Audio backend | PortAudio | system | Cross-platform audio hardware abstraction |
| Async runtime | `asyncio` | stdlib | Concurrent mic send + event receive |
| Config | `python-dotenv` | 1.2.2 | Loads API key from `.env` |
| Python | CPython | 3.11 | Runtime |

---

## File Reference

### `agents.py`

Defines the three-agent system using `google.adk.agents.Agent`.

```
Agent(
    name        – unique identifier, used in logs and tool-call routing
    model       – Gemini model string
    description – used by the orchestrator to decide when to delegate
    instruction – system prompt injected at the start of each session
    tools       – list of ADK tool objects the agent may call
    sub_agents  – list of child Agent objects (orchestrator only)
)
```

**Key design decisions:**

- The orchestrator uses `gemini-2.0-flash-live-001` — the only Gemini model
  that supports real-time bidirectional audio streaming via the Live API.
- Sub-agents use `gemini-2.0-flash` (text model). They never handle audio
  directly; the orchestrator translates between voice and text internally.
- Sub-agent routing happens via ADK's internal tool-call mechanism: the
  orchestrator emits a function call whose name matches a sub-agent's name,
  the ADK runner executes that sub-agent, and the result is returned as a
  function response — identical to how a regular tool works.

---

### `voice_io.py`

Thin wrapper around PyAudio with two independent streams.

| Parameter | Input stream | Output stream |
|---|---|---|
| Sample rate | 16 000 Hz | 24 000 Hz |
| Channels | 1 (mono) | 1 (mono) |
| Bit depth | 16-bit PCM | 16-bit PCM |
| Chunk size | 1 024 frames | written as-received |

**Why different sample rates?**
Gemini Live expects microphone input at 16 kHz (standard telephony rate).
It synthesises speech output at 24 kHz, which is the rate of its built-in TTS.
Mismatching these causes chipmunk or slow-motion playback artefacts.

---

### `main.py`

Orchestrates the asyncio event loop.

#### Session bootstrap

```python
InMemorySessionService.create_session(app_name, user_id, session_id)
```

A session holds the conversation state for one run. The triple
`(app_name, user_id, session_id)` uniquely identifies it. Using a fixed
`session_id` means re-running the script reuses the same logical session slot
(the in-memory service resets on process restart anyway).

#### LiveRequestQueue

```python
live_queue = LiveRequestQueue()
live_queue.send_realtime(Blob(data=bytes, mime_type="audio/pcm;rate=16000"))
live_queue.close()   # signals end-of-stream to the runner
```

The queue is a thread-safe channel between the mic-reading task and the ADK
runner. `send_realtime()` is non-blocking; the runner drains it continuously.

#### RunConfig

```python
RunConfig(
    response_modalities=["AUDIO"],       # tell Gemini to return audio, not text
    speech_config=SpeechConfig(
        voice_config=VoiceConfig(
            prebuilt_voice_config=PrebuiltVoiceConfig(voice_name="Puck")
        )
    ),
)
```

Available prebuilt voices: `Puck`, `Charon`, `Kore`, `Fenrir`, `Aoede`.

#### run_live async generator

```python
async for event in runner.run_live(
    user_id=..., session_id=...,
    live_request_queue=live_queue,
    run_config=run_config,
):
    ...
```

Each `Event` may carry:

| Field | Type | When present |
|---|---|---|
| `content.parts[*].inline_data` | `Blob` | Audio response chunk |
| `output_transcription.text` | `str` | Agent's words as text |
| `input_transcription.text` | `str` | Your words as text |
| `turn_complete` | `bool` | Agent finished speaking |
| `interrupted` | `bool` | User started speaking mid-reply |

#### Concurrency pattern

```
asyncio.create_task(send_audio())   ← runs concurrently
await receive_events()              ← drives the event loop
```

`send_audio()` calls `audio.read_chunk()` inside `run_in_executor()` because
`PyAudio.read()` is a blocking C call. Without the executor it would freeze
the event loop and starve the receive coroutine, causing audio dropouts.

---

## ADK Multi-Agent Routing — How It Works Internally

When the orchestrator decides a sub-agent should handle a request, ADK does
the following automatically:

```
1. Orchestrator LLM emits a function call:
   { "name": "research_agent", "args": { "request": "What is the speed of light?" } }

2. ADK runner intercepts this call (it is not sent to any external API).

3. ADK creates a new invocation of research_agent with the provided request
   as its user message.

4. research_agent calls google_search if needed, synthesises an answer,
   and returns it as a function response.

5. ADK injects the response back into the orchestrator's context:
   { "name": "research_agent", "response": { "result": "299 792 458 m/s …" } }

6. Orchestrator LLM reads the response and speaks the final answer.
```

This means sub-agents behave exactly like tools from the orchestrator's
perspective, but they have their own model, instructions, and tool access.

---

## Audio Format Cheat Sheet

```
Microphone → Gemini Live
  mime_type : audio/pcm;rate=16000
  encoding  : signed 16-bit little-endian
  channels  : 1 (mono)
  chunk     : 1024 frames = 64 ms of audio

Gemini Live → Speaker
  mime_type : audio/pcm  (24 kHz implied by Gemini TTS)
  encoding  : signed 16-bit little-endian
  channels  : 1 (mono)
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Gemini API key from aistudio.google.com |

---

## Known Limitations

| Limitation | Detail |
|---|---|
| In-memory session | Conversation history lost on process exit |
| Single user | SESSION_ID is hardcoded; multi-user needs dynamic session IDs |
| No VAD tuning | Uses Gemini's default voice activity detection |
| Sub-agent tools | `google_search` requires the API key to have Search API access |
| Model availability | `gemini-2.0-flash-live-001` may require allowlist access |

---

## Extending the System

**Add a new sub-agent:**
```python
# agents.py
calendar_agent = Agent(
    name="calendar_agent",
    model="gemini-2.0-flash",
    description="Manages calendar events and scheduling.",
    instruction="...",
    tools=[your_calendar_tool],
)

root_agent = Agent(
    ...
    sub_agents=[research_agent, task_agent, calendar_agent],
)
```

**Persist sessions across restarts:**
```python
# Replace InMemorySessionService with a database-backed one
from google.adk.sessions import DatabaseSessionService
session_service = DatabaseSessionService(db_url="sqlite:///sessions.db")
```

**Change the voice:**
```python
PrebuiltVoiceConfig(voice_name="Aoede")  # or Charon, Kore, Fenrir
```
