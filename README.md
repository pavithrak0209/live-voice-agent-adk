# 🎙️ Live Voice Agent with Google ADK

A real-time multi-agent voice system built with **Google's Agent Development Kit (ADK)** and **Gemini Live API**. Speak into your microphone — the agent listens, reasons, and talks back instantly.

---

## 🏗️ Architecture

```
voice_orchestrator  (root — gemini-2.0-flash-live-001)
│   Real-time bidirectional audio via Gemini Live API
│
├── research_agent  (gemini-2.0-flash)
│       Answers factual questions using Google Search
│
└── task_agent  (gemini-2.0-flash)
        Handles math, unit conversions, reminders & to-do lists
```

The orchestrator uses the **Gemini Live model** for real-time voice I/O (ASR + TTS built-in). Sub-agents run on the standard Flash model and are routed to automatically based on the user's intent.

---

## 📁 Project Structure

```
live-voice-agent-adk/
├── src/
│   ├── agents.py       # Agent definitions (orchestrator + sub-agents)
│   ├── main.py         # Entry point — asyncio event loop, mic & speaker
│   └── voice_io.py     # PyAudio wrapper for microphone input & speaker output
├── doc/
│   ├── architecture.md # System architecture & data flow diagrams
│   └── technical.md    # Full technical reference & API details
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PortAudio (required by PyAudio)
  ```bash
  # macOS
  brew install portaudio

  # Ubuntu / Debian
  sudo apt-get install portaudio19-dev
  ```
- A [Google API Key](https://aistudio.google.com/) with Gemini access

### Installation

```bash
git clone https://github.com/pavithrak0209/live-voice-agent-adk.git
cd live-voice-agent-adk

pip install google-adk google-genai pyaudio python-dotenv
```

### Configuration

Create a `.env` file in the root:

```env
GOOGLE_API_KEY=your_api_key_here
```

### Run

```bash
python src/main.py
```

Speak into your microphone. Press `Ctrl+C` to stop.

---

## ✨ Features

- 🎙️ **Real-time voice I/O** — microphone input + speaker output with no perceptible delay
- 🤖 **Multi-agent routing** — orchestrator delegates to the right specialist agent automatically
- 🔍 **Web search** — research agent uses Google Search for up-to-date answers
- 🧠 **Session memory** — conversation context is maintained within a session
- 🔊 **Gemini TTS** — natural-sounding voice responses using the "Puck" voice
- ⚡ **Async architecture** — non-blocking mic capture and event streaming with asyncio

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Agent Framework | Google ADK 2.1.0 |
| Voice Model | Gemini 2.0 Flash Live |
| Reasoning Models | Gemini 2.0 Flash |
| Audio I/O | PyAudio + PortAudio |
| Async Runtime | Python asyncio |
| Config | python-dotenv |

---

## 📖 Documentation

- [`doc/architecture.md`](doc/architecture.md) — System design, data flow, threading model
- [`doc/technical.md`](doc/technical.md) — Full API reference, audio formats, extending the system

---

## 🔭 Extending

**Add a new sub-agent** (e.g. calendar assistant):

```python
# src/agents.py
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

**Change the voice:**
```python
PrebuiltVoiceConfig(voice_name="Aoede")  # Puck | Charon | Kore | Fenrir | Aoede
```

**Persist sessions across restarts:**
```python
from google.adk.sessions import DatabaseSessionService
session_service = DatabaseSessionService(db_url="sqlite:///sessions.db")
```

---

## 📜 License

MIT
