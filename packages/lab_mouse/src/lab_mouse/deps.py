"""Agent dependency container."""

import os
from dataclasses import dataclass, field

_DEFAULT_MODEL = "ollama:phi4-mini:3.8b"

_SYSTEM_PROMPT = """\
You are a resume assistant for Franco Donadio. You have access to MCP tools \
that let you read and search his resume documents.

IMPORTANT: You MUST call the available tools to retrieve information. \
Never invent or assume resume content — always call a tool first.

Workflow:
1. To explore what's available → call md_list_sections(document=...).
2. To answer a question → call md_query(document=..., search_term=<keyword>).

After receiving tool results, synthesise them into a clear, direct answer.\
"""


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
    system_prompt: str = field(default=_SYSTEM_PROMPT)
    username: str = field(default_factory=lambda: os.getenv("TUI_UNAME", "((o))"))
    mcp_headers: dict[str, str] = field(default_factory=dict)
    context_window: int = 32_768
