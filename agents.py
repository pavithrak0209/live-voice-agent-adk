"""
Multi-agent voice system using Google ADK + Gemini Live API.

Architecture:
  root_agent (orchestrator, voice I/O)
    ├── research_agent  – answers factual / search questions
    └── task_agent      – handles reminders, lists, calculations
"""

from google.adk.agents import Agent
from google.adk.tools import google_search


# ── Sub-agent: Research ──────────────────────────────────────────────────────

research_agent = Agent(
    name="research_agent",
    model="gemini-2.0-flash",
    description="Answers factual questions and searches the web for current information.",
    instruction="""
You are a research assistant. When given a question:
1. Use the google_search tool to find accurate, up-to-date information.
2. Summarise the answer in 2-3 clear sentences.
3. Always cite your source briefly (e.g. "According to Wikipedia…").
Keep answers concise — this is a voice conversation.
""",
    tools=[google_search],
)


# ── Sub-agent: Task Assistant ─────────────────────────────────────────────────

task_agent = Agent(
    name="task_agent",
    model="gemini-2.0-flash",
    description="Handles tasks: calculations, unit conversions, setting reminders, and managing lists.",
    instruction="""
You are a task assistant. You help with:
- Math and unit conversions (compute the answer directly)
- Reminders (acknowledge and confirm the reminder)
- To-do lists (track items in the conversation)
Keep responses short and action-oriented — this is a voice conversation.
""",
)


# ── Root orchestrator (voice-enabled) ─────────────────────────────────────────

root_agent = Agent(
    name="voice_orchestrator",
    model="gemini-2.0-flash-live-001",   # Gemini Live for real-time voice
    description="Voice orchestrator that routes user requests to the right sub-agent.",
    instruction="""
You are a helpful voice assistant. Listen to the user and decide:
- For factual questions, web lookups, or "what is / who is / latest news" → delegate to research_agent.
- For tasks like calculations, reminders, or lists → delegate to task_agent.
- For casual conversation or greetings → handle it yourself.

Always respond naturally as if speaking aloud. Keep responses under 3 sentences unless more detail is explicitly requested.
""",
    sub_agents=[research_agent, task_agent],
)
