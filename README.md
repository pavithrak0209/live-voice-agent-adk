<div align="center">

# 🎙️ Live Voice Agent — Google ADK

**A production-grade, real-time multi-agent voice system powered by Google's Agent Development Kit and Gemini Live API**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-2.1.0-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://google.github.io/adk-docs/)
[![Gemini](https://img.shields.io/badge/Gemini%202.0%20Flash%20Live-8E44AD?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

<br/>

> **Speak. Think. Respond.** — in real time.

A voice agent that captures microphone input, streams it to Gemini Live, routes intent to specialist sub-agents, and plays back a natural voice response — all with sub-second latency.

<br/>

[🚀 Quick Start](#-quick-start) · [🏗️ Architecture](#%EF%B8%8F-architecture) · [✨ Features](#-features) · [📖 Docs](#-documentation)

</div>

---

## 🎯 What This Project Does

| You say... | Agent routes to... | Response |
|---|---|---|
| *"What's the latest news on AI?"* | 🔍 **Research Agent** → Google Search | Spoken summary with source |
| *"What's 15% of 348?"* | 🧮 **Task Agent** → inline reasoning | Instant spoken answer |
| *"Add milk to my shopping list"* | 🧮 **Task Agent** → list tracking | Confirms and remembers |
| *"Hey, how are you?"* | 🎙️ **Orchestrator** → direct reply | Natural conversation |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Your Machine                             │
│                                                                 │
│  🎙 Microphone                                   🔊 Speaker    │
│      │  PCM 16kHz                    PCM 24kHz        ▲        │
│      ▼                                                │        │
│  ┌─────────┐    LiveRequestQueue    ┌───────────────────────┐  │
│  │voice_io │ ─────────────────────▶│   Runner.run_live()   │  │
│  │(PyAudio)│◀─────────────────────-│   (async generator)   │  │
│  └─────────┘    audio events        └──────────┬────────────┘  │
└─────────────────────────────────────────────────│───────────────┘
                                                  │ WebSocket
                                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Google Cloud — Gemini API                  │
│                                                                 │
│         ┌──────────────────────────────────────────┐           │
│         │       voice_orchestrator (root)           │           │
│         │    gemini-2.0-flash-live-001              │           │
│         │    Built-in ASR  ·  Built-in TTS          │           │
│         └───────────────┬──────────────┬───────────┘           │
│                         │              │                        │
│            ┌────────────▼──┐    ┌──────▼────────────┐          │
│            │research_agent │    │   task_agent       │          │
│            │gemini-2.0-    │    │   gemini-2.0-flash │          │
│            │flash          │    │                    │          │
│            │[google_search]│    │  [inline reasoning]│          │
│            └───────────────┘    └────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Hierarchy

```
voice_orchestrator          ← root, handles all voice I/O
├── research_agent          ← factual Q&A, web search, current events
└── task_agent              ← math, conversions, reminders, lists
```

Sub-agents are routed via **ADK's internal tool-call mechanism** — the orchestrator treats each sub-agent like a tool, calls it with the user's request, and speaks the result. Zero custom routing logic needed.

---

## ✨ Features

- 🎙️ **Real-time bidirectional voice** — PCM audio streamed live, no wait time
- 🤖 **Intelligent multi-agent routing** — orchestrator delegates to the right specialist automatically
- 🔍 **Live web search** — research agent queries Google Search for current information
- 🧠 **Session memory** — full conversation context maintained across turns
- 🔊 **Natural TTS** — Gemini's built-in text-to-speech with multiple voice options
- ⚡ **Async-first architecture** — non-blocking mic capture via `run_in_executor`, event streaming with asyncio
- 🛡️ **Graceful shutdown** — `Ctrl+C` cleanly cancels tasks, drains queues, and closes audio streams

---

## 📁 Project Structure

```
live-voice-agent-adk/
│
├── src/
│   ├── agents.py       # All agent definitions — orchestrator + sub-agents
│   ├── main.py         # Entry point: asyncio loop, mic/speaker, session bootstrap
│   └── voice_io.py     # PyAudio wrapper (16kHz input · 24kHz output)
│
├── doc/
│   ├── architecture.md # Deep-dive: system design, data flow, threading model
│   └── technical.md    # API reference, audio formats, extending the system
│
└── README.md
```

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# macOS
brew install portaudio

# Ubuntu / Debian
sudo apt-get install portaudio19-dev
```

Get a free API key at [aistudio.google.com](https://aistudio.google.com)

### 2. Install

```bash
git clone https://github.com/pavithrak0209/live-voice-agent-adk.git
cd live-voice-agent-adk
pip install google-adk google-genai pyaudio python-dotenv
```

### 3. Configure

```bash
echo "GOOGLE_API_KEY=your_key_here" > .env
```

### 4. Run

```bash
python src/main.py
```

```
=== Voice Agent Ready ===
Speak into your microphone. Press Ctrl+C to stop.

You:   What's the capital of Japan?
Agent: The capital of Japan is Tokyo. According to Wikipedia, it's one of...
```

---

## 🛠️ Tech Stack

| Layer | Technology | Role |
|---|---|---|
| 🤖 Agent Framework | Google ADK 2.1.0 | Agent orchestration, tool routing, live runner |
| 🧠 Voice Model | Gemini 2.0 Flash Live | Real-time audio streaming, ASR, TTS |
| ⚡ Reasoning | Gemini 2.0 Flash | Sub-agent reasoning & tool execution |
| 🎙️ Audio I/O | PyAudio + PortAudio | Mic capture (16kHz) · Speaker playback (24kHz) |
| 🔄 Async Runtime | Python asyncio | Concurrent send/receive without threading |
| 🔑 Config | python-dotenv | API key management |

---

## 🔭 Extending the System

**Add a new sub-agent:**
```python
# src/agents.py
calendar_agent = Agent(
    name="calendar_agent",
    model="gemini-2.0-flash",
    description="Manages calendar events and scheduling.",
    instruction="You help users schedule and manage events...",
    tools=[your_calendar_tool],
)

root_agent = Agent(..., sub_agents=[research_agent, task_agent, calendar_agent])
```

**Switch voice:**
```python
PrebuiltVoiceConfig(voice_name="Aoede")  # Puck | Charon | Kore | Fenrir | Aoede
```

**Persist memory across sessions:**
```python
from google.adk.sessions import DatabaseSessionService
session_service = DatabaseSessionService(db_url="sqlite:///sessions.db")
```

---

## 📖 Documentation

| Doc | Description |
|---|---|
| [`doc/architecture.md`](doc/architecture.md) | System design, full data flow diagram, threading model, session management |
| [`doc/technical.md`](doc/technical.md) | API reference, audio format specs, agent routing internals, known limitations |

---

## 🎓 Built as part of

**"Building Live Voice Agents with Google's ADK"** — DeepLearning.AI
Instructors: Lavi Nigam & Sita Lakshmi Sangameswaran, ML Engineers at Google

---

<div align="center">

Made with ❤️ by [Pavithra Kannan](https://github.com/pavithrak0209)

</div>
