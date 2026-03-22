"""Single source of truth for TUI render state.

Components read this state; only BaseTuiApp._handle_event() writes it.
Conversation messages are NOT stored here — they are owned by HistoryControl.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# Exactly two valid panel states — no boolean flag combinations possible.
ActivePanel = Literal["main", "logs", "internal_logs"]


@dataclass
class TuiState:
    """Shared UI state passed by reference into every component."""

    thinking: bool = False
    mcp_connected: bool = False
    mcp_server_url: str = ""
    mcp_server_headers: dict[str, str] = field(default_factory=dict)
    agent_name: str = ""
    model_name: str = ""
    username: str = "((o))"
    loader_frame: int = 0
    log_lines: list[str] = field(default_factory=list)
    internal_log_lines: list[str] = field(default_factory=list)
    active_panel: ActivePanel = "main"
    context_tokens_used: int = 0
    context_tokens_max: int = 32_768
    active_levels: set[str] = field(default_factory=lambda: {"ERR", "DBG"})
    show_model_selector: bool = False
    available_models: list[str] = field(default_factory=list)
    model_selector_idx: int = 0
    detail_mode: bool = False
    detail_tool_idx: int = -1  # -1 = show message summary; ≥0 = tool call index within selected turn
    show_help: bool = False
