"""Scrollable conversation history control.

HistoryControl owns its own message list.  All mutations go through its
public methods (add_user_message, append_delta, etc.); nothing outside
this class writes to _messages or _streaming.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field
from typing import Literal

from prompt_toolkit.application import get_app
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.layout.controls import FormattedTextControl

from ..state import TuiState

_BOLD_RE = re.compile(r"\*([^*\n]+)\*")

_CURSOR = "\u258b"  # ▋ block cursor glyph shown while streaming
_SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
_BAR = "\u258f "   # ▏ thin left-border glyph + space
_GUTTER_WIDTH = len(_BAR)  # 2 — subtracted from terminal width when wrapping


def _render_inline(text: str, base: str, bold: str) -> StyleAndTextTuples:
    """Return styled fragments for *text*, highlighting ``*...*`` spans as bold."""
    result: StyleAndTextTuples = []
    last = 0
    for m in _BOLD_RE.finditer(text):
        if m.start() > last:
            result.append((base, text[last:m.start()]))
        result.append((bold, m.group(1)))
        last = m.end()
    if last < len(text):
        result.append((base, text[last:]))
    return result or [(base, text)]


def _visual_lines(text: str, width: int) -> list[str]:
    """Split *text* into visual lines of at most *width* columns."""
    if not text:
        return [""]
    return textwrap.wrap(text, width=width, break_long_words=True, break_on_hyphens=False) or [""]


@dataclass
class MessageView:
    """One rendered message in the conversation history."""

    role: Literal["user", "agent", "tool"]
    agent_id: str
    content: str
    complete: bool = False


@dataclass
class _StreamingMessage:
    """In-progress agent response being built delta by delta."""

    agent_id: str
    content: str = field(default="")


class HistoryControl(FormattedTextControl):
    """Renders conversation messages as formatted text fragments.

    User messages appear with a grey left-border gutter, agent messages
    with a coloured gutter.  Long lines are manually wrapped so that the
    gutter character appears on every visual row.
    """

    def __init__(self, state: TuiState) -> None:
        self._state = state
        self._messages: list[MessageView] = []
        self._streaming: _StreamingMessage | None = None
        self._current_agent_id: str = "main"
        super().__init__(self._get_fragments)

    # ------------------------------------------------------------------
    # Mutation API — called only from BaseTuiApp._handle_event

    def add_user_message(self, content: str, agent_id: str = "main") -> None:
        """Append a completed user message."""
        self._messages.append(MessageView(role="user", agent_id=agent_id, content=content, complete=True))

    def start_agent_stream(self, agent_id: str = "main") -> None:
        """Signal that an agent response is about to stream in."""
        self._current_agent_id = agent_id

    def append_delta(self, content: str) -> None:
        """Append a text chunk to the in-progress agent response."""
        if self._streaming is None:
            self._streaming = _StreamingMessage(agent_id=self._current_agent_id)
        self._streaming.content += content

    def end_agent_stream(self, final_output: str = "") -> None:
        """Finalise the in-progress agent response and move it to history."""
        content = final_output or (self._streaming.content if self._streaming else "")
        agent_id = self._streaming.agent_id if self._streaming else self._current_agent_id
        if content:
            self._messages.append(
                MessageView(role="agent", agent_id=agent_id, content=content, complete=True)
            )
        self._streaming = None
        self._current_agent_id = "main"

    def add_tool_call(self, name: str) -> None:
        """Append an incomplete tool-call indicator row."""
        self._messages.append(
            MessageView(role="tool", agent_id="main", content=f"\u2699 {name}\u2026", complete=False)
        )

    def complete_last_tool(self) -> None:
        """Mark the most recent incomplete tool row as complete."""
        for msg in reversed(self._messages):
            if msg.role == "tool" and not msg.complete:
                msg.complete = True
                break

    def clear(self) -> None:
        """Clear all messages and any in-progress stream."""
        self._messages.clear()
        self._streaming = None
        self._current_agent_id = "main"

    # ------------------------------------------------------------------
    # Rendering

    def _get_fragments(self) -> StyleAndTextTuples:
        try:
            wrap_width = get_app().output.get_size().columns - _GUTTER_WIDTH
        except Exception:
            wrap_width = 78

        fragments: StyleAndTextTuples = []
        state = self._state

        for msg in self._messages:
            if msg.role == "user":
                for line in (msg.content.splitlines() or [""]):
                    for vline in _visual_lines(line, wrap_width):
                        fragments.append(("class:msg.gutter.user", _BAR))
                        fragments.append(("class:msg.user", vline + "\n"))
                fragments.append(("class:msg.gutter.user", _BAR + "\n"))
                fragments.append(("", "\n"))
            elif msg.role == "agent":
                for line in (msg.content.splitlines() or [""]):
                    for vline in _visual_lines(line, wrap_width):
                        fragments.append(("class:msg.gutter.agent", _BAR))
                        fragments.extend(_render_inline(vline, "class:msg.agent", "class:msg.agent.bold"))
                        fragments.append(("class:msg.agent", "\n"))
                fragments.append(("class:msg.gutter.agent", _BAR + "\n"))
                fragments.append(("", "\n"))
            elif msg.role == "tool":
                style = "class:msg.tool.done" if msg.complete else "class:msg.tool"
                fragments.append((style, "  " + msg.content + "\n"))

        if state.thinking:
            if self._streaming and self._streaming.content:
                for line in (self._streaming.content.splitlines() or [""]):
                    for vline in _visual_lines(line, wrap_width):
                        fragments.append(("class:msg.gutter.agent", _BAR))
                        fragments.extend(_render_inline(vline, "class:msg.agent", "class:msg.agent.bold"))
                        fragments.append(("class:msg.agent", "\n"))
                fragments.append(("class:msg.cursor", _CURSOR + "\n\n"))
            else:
                spinner = _SPINNER_FRAMES[state.loader_frame % len(_SPINNER_FRAMES)]
                fragments.append(("class:msg.gutter.agent", _BAR))
                fragments.append(("class:msg.agent", spinner + "\n\n"))

        return fragments
