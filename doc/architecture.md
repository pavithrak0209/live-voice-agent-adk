# Architecture — Live Multi-Agent Voice System

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User's Machine                           │
│                                                                 │
│   🎙 Microphone                              🔊 Speaker        │
│       │                                           ▲             │
│       ▼                                           │             │
│  ┌──────────┐   PCM audio chunks   ┌────────────────────────┐  │
│  │ voice_io │ ──────────────────▶  │   LiveRequestQueue     │  │
│  │ (PyAudio)│                      │   (ADK in-process)     │  │
│  └──────────┘                      └───────────┬────────────┘  │
│       ▲                                        │               │
│       │ PCM audio                              ▼               │
│       │ (inline_data)             ┌────────────────────────┐   │
│       └───────────────────────── │    Runner.run_live()    │   │
│                                  │    (async generator)    │   │
│                                  └───────────┬────────────┘   │
└──────────────────────────────────────────────│─────────────────┘
                                               │ WebSocket / gRPC
                                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Google Cloud (Gemini API)                  │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │              voice_orchestrator                          │  │
│   │         (gemini-2.0-flash-live-001)                      │  │
│   │                                                          │  │
│   │   Real-time bidirectional audio streaming                │  │
│   │   Automatic speech recognition (ASR) built-in           │  │
│   │   Text-to-speech synthesis (TTS) built-in               │  │
│   │                                                          │  │
│   │   Routes to sub-agents via ADK tool-call mechanism:     │  │
│   │                                                          │  │
│   │   ┌──────────────────┐   ┌──────────────────────────┐   │  │
│   │   │  research_agent  │   │      task_agent           │   │  │
│   │   │ gemini-2.0-flash │   │   gemini-2.0-flash        │   │  │
│   │   │                  │   │                           │   │  │
│   │   │  [google_search] │   │  (inline reasoning)       │   │  │
│   │   └──────────────────┘   └──────────────────────────┘   │  │
│   └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent Hierarchy

```
voice_orchestrator  (root)
│   Model : gemini-2.0-flash-live-001
│   I/O   : real-time audio (mic → Gemini → speaker)
│
├── research_agent  (sub-agent)
│   │   Model : gemini-2.0-flash
│   │   Tool  : google_search
│   └── Triggered for: factual questions, current events, "what is / who is"
│
└── task_agent  (sub-agent)
        Model : gemini-2.0-flash
        Tools : none (pure reasoning)
        Triggered for: math, unit conversions, to-do lists, reminders
```

---

## Data Flow — One Turn

```
1. CAPTURE
   PyAudio reads 1024-frame PCM chunks from the microphone (16 kHz, mono, 16-bit)

2. SEND
   Each chunk is wrapped in a Blob(mime_type="audio/pcm;rate=16000")
   and pushed into the LiveRequestQueue via send_realtime()

3. STREAM TO GEMINI
   The ADK Runner forwards chunks over a persistent WebSocket connection
   to the Gemini Live API endpoint

4. ASR (automatic speech recognition — cloud-side)
   Gemini Live transcribes the incoming PCM stream in real time
   input_transcription events are emitted back to the client

5. ROUTING (orchestrator reasoning — cloud-side)
   voice_orchestrator decides:
     → casual chat           → answer inline
     → factual / web query   → delegate to research_agent
     → task / calculation    → delegate to task_agent

6. SUB-AGENT EXECUTION (if delegated)
   ADK issues an internal tool call to the chosen sub-agent
   The sub-agent may call google_search, then returns a text result
   The orchestrator incorporates that result into its spoken reply

7. TTS (text-to-speech — cloud-side)
   Gemini synthesises a PCM audio response (24 kHz, mono, 16-bit, voice "Puck")

8. RECEIVE
   Runner.run_live() yields Event objects containing inline_data audio blobs

9. PLAYBACK
   main.py extracts each blob and writes it to the PyAudio output stream
   output_transcription events are printed to the terminal for visibility
```

---

## Session & State Management

```
InMemorySessionService
│
└── Session(app_name, user_id, session_id)
        Stores the conversation history for the current run
        Lost when the process exits (swap for VertexAI session service
        or a database-backed service for persistent memory)
```

---

## Threading Model

```
Python asyncio event loop
│
├── Task: send_audio()      — runs in a ThreadPoolExecutor
│         PyAudio.read() is blocking; run_in_executor() prevents it
│         from blocking the event loop
│
└── Coroutine: receive_events()
          Async for-loop over Runner.run_live() async generator
          Writes audio and prints transcriptions synchronously
          (PyAudio.write() is fast enough not to need an executor here)
```
