"""Agent dependency container."""

import os
import re
from dataclasses import dataclass, field

_DEFAULT_MODEL = "gemini-3-flash-preview"

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

_SMALL_MODEL_GUIDE = """
---
TOOL USE GUIDE (read carefully — you must follow this exactly):

You have exactly 2 tools. Always call one before answering.

TOOL 1 — md_list_sections
  When to use: when you need to know what sections exist.
  Required argument:
    document: one of "RESUME", "RESUME_CREATIVE", "RESUME_EXTENDED"
  Example call:
    md_list_sections(document="RESUME")

TOOL 2 — md_query
  When to use: when you need to read content about a topic.
  Required arguments:
    document: one of "RESUME", "RESUME_CREATIVE", "RESUME_EXTENDED"
    search_term: a single keyword from the user's question
  Optional argument:
    max_sections: integer 1–5 (default 3)
  Example call:
    md_query(document="RESUME", search_term="experience")

Rules you must never break:
- Always supply BOTH required arguments to md_query.
- document must be exactly one of the three strings above — no variations.
- search_term must be a single keyword, not a sentence.
- Never answer from memory. Always call a tool first.
- If the tool returns no results, try a shorter search_term and call again.
"""


# Matches model names that suggest a small parameter count (≤ 2 B params)
# or known small-model variant keywords.
_SMALL_MODEL_RE = re.compile(
    r"\b0\.\d+b\b"           # 0.5b, 0.6b, 0.7b …
    r"|\b1(?:\.\d+)?b\b"     # 1b, 1.5b, 1.7b …
    r"|\b2(?:\.\d+)?b\b"     # 2b, 2.1b …
    r"|mini|tiny|nano|small", # named small variants
    re.IGNORECASE,
)


def _is_small_model(model: str) -> bool:
    return bool(_SMALL_MODEL_RE.search(model))


def build_system_prompt(model: str) -> str:
    """Return the system prompt, appending the tool-use guide for small models."""
    if _is_small_model(model):
        return _SYSTEM_PROMPT + _SMALL_MODEL_GUIDE
    return _SYSTEM_PROMPT


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
    system_prompt: str = field(default="")  # set in __post_init__ based on model
    username: str = field(default_factory=lambda: os.getenv("TUI_UNAME", "((o))"))
    mcp_headers: dict[str, str] = field(default_factory=dict)
    context_window: int = 32_768

    def __post_init__(self) -> None:
        if not self.system_prompt:
            self.system_prompt = build_system_prompt(self.model)
