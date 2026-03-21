"""Single source of truth for the TUI.

Components are pure render functions — they read state, never write it.
Only ``TuiApp`` mutates state and then calls ``app.invalidate()``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# Exactly three valid panel states — no boolean flag combinations possible.
ActivePanel = Literal["main", "logs"]


@dataclass
class Message:
    """A single conversation entry."""

    role: Literal["user", "agent", "tool"]
    content: str
    complete: bool = False


@dataclass
class TuiState:
    """Shared UI state passed by reference into every component."""

    messages: list[Message] = field(default_factory=list)
    thinking: bool = False
    mcp_connected: bool = False
    model_name: str = ""
    current_agent_text: str = ""
    username: str = "((o))"
    loader_frame: int = 0
    log_lines: list[str] = field(default_factory=list)
    active_panel: ActivePanel = "main"
    context_tokens_used: int = 0
    context_tokens_max: int = 32_768

