"""Agent dependency container."""

import os
from dataclasses import dataclass, field

_DEFAULT_MODEL = "ollama:phi4-mini:3.8b"


@dataclass
class AgentDeps:
    """Runtime dependencies injected into the agent.

    Attributes:
        model: Pydantic-AI model string (e.g. ``"openai:gpt-4o"``).
        server_url: Base URL of the MCP server's SSE/HTTP endpoint.
        system_prompt: System instruction passed to the LLM on every run.
        username: Display name shown in the TUI for user messages.
    """

    model: str = field(default_factory=lambda: os.getenv("AGENT_MODEL", _DEFAULT_MODEL))
    server_url: str = field(default="http://127.0.0.1:8000/mcp")
    system_prompt: str = field(default="/no_think You are a helpful assistant with access to MCP tools.")
    username: str = field(default_factory=lambda: os.getenv("TUI_UNAME", "((o))"))
    context_window: int = 32_768
