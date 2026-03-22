"""Scrollable conversation history control.

HistoryControl owns its own message list.  All mutations go through its
public methods (add_user_message, append_delta, etc.); nothing outside
this class writes to _messages or _streaming.
"""

from __future__ import annotations

import json
import re
import textwrap
import time
from dataclasses import dataclass, field
from typing import Literal

from prompt_toolkit.application import get_app
from prompt_toolkit.data_structures import Point
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
    tool_args: dict = field(default_factory=dict)
    tool_result: str = ""
    response_time_ms: float = 0.0   # wall-clock ms from start_agent_stream → end_agent_stream
    tokens_used: int = 0            # token delta for this response (set by receive_tokens)


@dataclass
class _Turn:
    """Logical conversation turn: user → tools → agent."""

    user_idx: int | None
    tool_idxs: list[int]
    agent_idx: int | None


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
        self._line_count: int = 0
        self._scroll_offset: int = 0  # lines from the bottom; 0 = follow latest
        self._cursor_idx: int = -1    # -1 = auto-follow latest; ≥0 = selected message index
        self._stream_start_time: float = 0.0
        self._pending_tokens: int = 0   # tokens received before AgentEndEvent (beetle order)
        super().__init__(self._get_fragments, get_cursor_position=self._cursor_pos)

    @property
    def cursor_active(self) -> bool:
        return self._cursor_idx >= 0

    def _cursor_pos(self) -> Point:
        """Return the cursor position used by the window to determine scroll target."""
        if self._cursor_idx >= 0 and hasattr(self, "_cursor_line"):
            return Point(x=0, y=self._cursor_line)
        target = max(0, self._line_count - 1 - self._scroll_offset)
        return Point(x=0, y=target)

    def scroll_up(self, lines: int = 3) -> None:
        """Scroll toward older messages."""
        self._scroll_offset = min(self._scroll_offset + lines, max(0, self._line_count - 1))

    def scroll_down(self, lines: int = 3) -> None:
        """Scroll toward the most recent message."""
        self._scroll_offset = max(0, self._scroll_offset - lines)

    # ------------------------------------------------------------------
    # Mutation API — called only from BaseTuiApp._handle_event

    def add_user_message(self, content: str, agent_id: str = "main") -> None:
        """Append a completed user message and snap the view to the bottom."""
        self._scroll_offset = 0
        self._messages.append(MessageView(role="user", agent_id=agent_id, content=content, complete=True))

    def start_agent_stream(self, agent_id: str = "main") -> None:
        """Signal that an agent response is about to stream in."""
        self._current_agent_id = agent_id
        self._stream_start_time = time.monotonic()
        self._pending_tokens = 0

    def append_delta(self, content: str) -> None:
        """Append a text chunk to the in-progress agent response."""
        if self._streaming is None:
            self._streaming = _StreamingMessage(agent_id=self._current_agent_id)
        self._streaming.content += content

    def end_agent_stream(self, final_output: str = "") -> None:
        """Finalise the in-progress agent response and move it to history."""
        elapsed_ms = (time.monotonic() - self._stream_start_time) * 1000.0
        content = final_output or (self._streaming.content if self._streaming else "")
        agent_id = self._streaming.agent_id if self._streaming else self._current_agent_id
        if content:
            self._messages.append(
                MessageView(
                    role="agent",
                    agent_id=agent_id,
                    content=content,
                    complete=True,
                    response_time_ms=elapsed_ms,
                    tokens_used=self._pending_tokens,
                )
            )
        self._streaming = None
        self._current_agent_id = "main"
        self._pending_tokens = 0

    def receive_tokens(self, delta: int) -> None:
        """Record the token delta for the most recent (or in-progress) agent turn.

        Called by the app when a ``TokenUsageEvent`` arrives.  Handles both
        orderings: beetle emits usage *before* ``AgentEndEvent``; lab_mouse
        emits it *after*.  In the "before" case the value is stored as
        ``_pending_tokens`` and consumed by ``end_agent_stream``.  In the
        "after" case it updates the already-created ``MessageView``.
        """
        self._pending_tokens = delta
        for msg in reversed(self._messages):
            if msg.role == "agent":
                msg.tokens_used = delta
                return

    def add_tool_call(self, name: str, args: dict | None = None) -> None:
        """Append an incomplete tool-call indicator row."""
        self._messages.append(
            MessageView(
                role="tool",
                agent_id="main",
                content=f"\u2699 {name}\u2026",
                complete=False,
                tool_args=args or {},
            )
        )

    def complete_last_tool(self, result: str = "") -> None:
        """Mark the most recent incomplete tool row as complete."""
        for msg in reversed(self._messages):
            if msg.role == "tool" and not msg.complete:
                msg.complete = True
                msg.tool_result = result
                break

    def clear(self) -> None:
        """Clear all messages and any in-progress stream."""
        self._messages.clear()
        self._streaming = None
        self._current_agent_id = "main"
        self._cursor_idx = -1
        self._state.detail_mode = False
        self._state.detail_tool_idx = -1

    # ------------------------------------------------------------------
    # Message cursor — Stage 1 navigation (Up/Down when input is empty)

    def cursor_prev(self) -> None:
        """Move cursor toward older messages; activates cursor if auto-following."""
        if not self._messages:
            return
        if self._cursor_idx < 0:
            self._cursor_idx = len(self._messages) - 1
        else:
            self._cursor_idx = max(0, self._cursor_idx - 1)
        self._state.detail_tool_idx = -1

    def cursor_next(self) -> None:
        """Move cursor toward newer messages; at last message resets to auto-follow."""
        if not self._messages:
            return
        if self._cursor_idx < 0:
            return
        if self._cursor_idx >= len(self._messages) - 1:
            self._cursor_idx = -1  # auto-follow latest
            self._state.detail_tool_idx = -1
        else:
            self._cursor_idx += 1
            self._state.detail_tool_idx = -1

    def follow_latest(self) -> None:
        """Reset cursor to auto-follow the latest message."""
        self._cursor_idx = -1
        self._state.detail_tool_idx = -1

    # ------------------------------------------------------------------
    # Inspect mode — Stage 2 navigation

    def enter_detail(self) -> None:
        """Enter inspect mode; lock cursor to current position."""
        if self._messages and self._cursor_idx < 0:
            self._cursor_idx = len(self._messages) - 1
        self._state.detail_mode = True
        self._state.detail_tool_idx = -1

    def exit_detail(self) -> None:
        """Exit inspect mode."""
        self._state.detail_mode = False
        self._state.detail_tool_idx = -1

    def detail_tool_prev(self) -> None:
        """Cycle tool cursor left within the selected turn."""
        tools = self._selected_turn_tools()
        if not tools:
            return
        n = len(tools)
        if self._state.detail_tool_idx < 0:
            self._state.detail_tool_idx = n - 1
        else:
            self._state.detail_tool_idx = (self._state.detail_tool_idx - 1) % n

    def detail_tool_next(self) -> None:
        """Cycle tool cursor right within the selected turn."""
        tools = self._selected_turn_tools()
        if not tools:
            return
        n = len(tools)
        if self._state.detail_tool_idx < 0:
            self._state.detail_tool_idx = 0
        else:
            self._state.detail_tool_idx = (self._state.detail_tool_idx + 1) % n

    def selected_message(self) -> MessageView | None:
        idx = self._cursor_idx if self._cursor_idx >= 0 else (len(self._messages) - 1)
        if 0 <= idx < len(self._messages):
            return self._messages[idx]
        return None

    def selected_tool(self) -> MessageView | None:
        tools = self._selected_turn_tools()
        if 0 <= self._state.detail_tool_idx < len(tools):
            return tools[self._state.detail_tool_idx]
        return None

    # ------------------------------------------------------------------
    # Turn grouping

    def _build_turns(self) -> list[_Turn]:
        """Group flat _messages into logical conversation turns."""
        turns: list[_Turn] = []
        current = _Turn(user_idx=None, tool_idxs=[], agent_idx=None)
        for i, msg in enumerate(self._messages):
            if msg.role == "user":
                if current.agent_idx is not None or current.tool_idxs:
                    turns.append(current)
                current = _Turn(user_idx=i, tool_idxs=[], agent_idx=None)
            elif msg.role == "tool":
                current.tool_idxs.append(i)
            elif msg.role == "agent":
                current.agent_idx = i
                turns.append(current)
                current = _Turn(user_idx=None, tool_idxs=[], agent_idx=None)
        if current.user_idx is not None or current.agent_idx is not None or current.tool_idxs:
            turns.append(current)
        return turns

    def _turn_for_idx(self, msg_idx: int) -> _Turn | None:
        """Return the turn that contains message at *msg_idx*."""
        for turn in self._build_turns():
            all_idxs = [i for i in [turn.user_idx, turn.agent_idx] + turn.tool_idxs if i is not None]
            if msg_idx in all_idxs:
                return turn
        return None

    def _selected_turn_tools(self) -> list[MessageView]:
        """Return tool messages in the same turn as the selected message."""
        idx = self._cursor_idx if self._cursor_idx >= 0 else (len(self._messages) - 1)
        turn = self._turn_for_idx(idx)
        if turn is None:
            return []
        return [self._messages[i] for i in turn.tool_idxs]

    def _adjacent_tools(self, idx: int) -> list[MessageView]:
        """Return tool messages in the same turn as _messages[idx]."""
        turn = self._turn_for_idx(idx)
        if turn is None:
            return []
        return [self._messages[i] for i in turn.tool_idxs]

    # ------------------------------------------------------------------
    # Inline detail rendering

    def _inline_detail(self, msg_idx: int, wrap_width: int) -> StyleAndTextTuples:
        """Return inspect-panel fragments rendered inline below the selected message.

        Compact (cursor active, detail_mode=False): one summary line.
        Expanded (F2 pressed, detail_mode=True): full metadata, tool args and results.
        """
        if msg_idx < 0 or msg_idx >= len(self._messages):
            return []
        msg = self._messages[msg_idx]
        state = self._state
        frags: StyleAndTextTuples = []
        sep = "  " + "\u2500" * min(wrap_width - 4, 48)
        frags.append(("class:detail.header", sep + "\n"))

        if not state.detail_mode:
            # ── compact: one summary line ─────────────────────────────────
            tools = self._adjacent_tools(msg_idx)
            if msg.role == "agent":
                summary = "  " + (msg.agent_id if msg.agent_id and msg.agent_id != "main" else "agent")
                if msg.response_time_ms > 0:
                    summary += f"  \u00b7  {msg.response_time_ms / 1000:.2f}s"
                if msg.tokens_used > 0:
                    summary += f"  \u00b7  {msg.tokens_used} tok"
                if tools:
                    summary += f"  \u00b7  {len(tools)} tool{'s' if len(tools) != 1 else ''}"
            elif msg.role == "tool":
                name = msg.content.lstrip("\u2699 ").rstrip("\u2026")
                summary = f"  tool  \u00b7  {name}"
                if msg.complete:
                    summary += "  \u2713"
            else:
                summary = "  user"
                if tools:
                    summary += f"  \u00b7  {len(tools)} tool{'s' if len(tools) != 1 else ''}"
            frags.append(("class:detail.key", summary + "\n"))
            frags.append(("class:detail.hint", "  F2  expand    Esc  clear\n"))
        else:
            # ── expanded: full details ────────────────────────────────────
            tool = self.selected_tool()
            if tool is not None:
                # specific tool call selected via Left/Right
                tools = self._selected_turn_tools()
                n = len(tools)
                tidx = state.detail_tool_idx
                name = tool.content.lstrip("\u2699 ").rstrip("\u2026")
                frags.append(("class:detail.header", f"  TOOL {tidx + 1}/{n}  \u00b7  {name}\n"))
                frags.append(("class:detail.key", "  Args    "))
                if tool.tool_args:
                    try:
                        args_str = json.dumps(tool.tool_args, indent=2)
                        if len(args_str) > 200:
                            args_str = args_str[:200] + "\u2026"
                    except Exception:
                        args_str = str(tool.tool_args)
                else:
                    args_str = "(none)"
                frags.append(("class:detail.val", args_str + "\n"))
                frags.append(("class:detail.key", "  Result  "))
                result = tool.tool_result
                if result:
                    result = result[:200] + "\u2026" if len(result) > 200 else result
                else:
                    result = "(pending\u2026)"
                frags.append(("class:detail.val", result + "\n"))
                frags.append(("class:detail.hint", "  \u2190 \u2192  cycle    F2  collapse    Esc  clear\n"))
            elif msg.role == "agent":
                # agent message metadata
                header = "  " + (msg.agent_id if msg.agent_id and msg.agent_id != "main" else "agent")
                if msg.response_time_ms > 0:
                    secs = msg.response_time_ms / 1000.0
                    header += f"  \u00b7  {secs:.2f}s ({msg.response_time_ms:.0f}ms)"
                if msg.tokens_used > 0:
                    header += f"  \u00b7  {msg.tokens_used} tok"
                frags.append(("class:detail.header", header + "\n"))
                tools = self._adjacent_tools(msg_idx)
                if tools:
                    done = sum(1 for t in tools if t.complete)
                    names = ", ".join(t.content.lstrip("\u2699 ").rstrip("\u2026") for t in tools)
                    frags.append(("class:detail.key", "  Tools   "))
                    frags.append(("class:detail.val", f"{done}/{len(tools)}  {names}\n"))
                    frags.append(("class:detail.hint", "  \u2190 \u2192  cycle tools    F2  collapse    Esc  clear\n"))
                else:
                    frags.append(("class:detail.key", "  Tools   "))
                    frags.append(("class:detail.val", "none\n"))
                    frags.append(("class:detail.hint", "  F2  collapse    Esc  clear\n"))
            elif msg.role == "tool":
                # tool row: show args + result
                name = msg.content.lstrip("\u2699 ").rstrip("\u2026")
                frags.append(("class:detail.header", f"  TOOL  \u00b7  {name}\n"))
                frags.append(("class:detail.key", "  Args    "))
                if msg.tool_args:
                    try:
                        args_str = json.dumps(msg.tool_args, indent=2)
                        if len(args_str) > 200:
                            args_str = args_str[:200] + "\u2026"
                    except Exception:
                        args_str = str(msg.tool_args)
                else:
                    args_str = "(none)"
                frags.append(("class:detail.val", args_str + "\n"))
                frags.append(("class:detail.key", "  Result  "))
                result = msg.tool_result if msg.tool_result else ("(pending\u2026)" if not msg.complete else "(none)")
                if len(result) > 200:
                    result = result[:200] + "\u2026"
                frags.append(("class:detail.val", result + "\n"))
                frags.append(("class:detail.hint", "  F2  collapse    Esc  clear\n"))
            else:
                # user message: show turn agent metadata
                tools = self._adjacent_tools(msg_idx)
                turn = self._turn_for_idx(msg_idx)
                turn_info = ""
                if turn and turn.agent_idx is not None:
                    agent_msg = self._messages[turn.agent_idx]
                    if agent_msg.response_time_ms > 0:
                        turn_info += f"  \u00b7  {agent_msg.response_time_ms / 1000:.2f}s"
                    if agent_msg.tokens_used > 0:
                        turn_info += f"  \u00b7  {agent_msg.tokens_used} tok"
                frags.append(("class:detail.header", f"  user{turn_info}\n"))
                if tools:
                    names = ", ".join(t.content.lstrip("\u2699 ").rstrip("\u2026") for t in tools)
                    frags.append(("class:detail.key", "  Tools   "))
                    frags.append(("class:detail.val", f"{len(tools)}  {names}\n"))
                frags.append(("class:detail.hint", "  F2  collapse    Esc  clear\n"))

        frags.append(("class:detail.header", sep + "\n"))
        return frags

    # ------------------------------------------------------------------
    # Rendering

    def _get_fragments(self) -> StyleAndTextTuples:
        try:
            wrap_width = get_app().output.get_size().columns - _GUTTER_WIDTH
        except Exception:
            wrap_width = 78

        fragments: StyleAndTextTuples = []
        state = self._state
        selected_idx = self._cursor_idx if self._cursor_idx >= 0 else -1

        cursor_line: int = 0
        line_counter = 0

        for i, msg in enumerate(self._messages):
            is_selected = selected_idx >= 0 and i == selected_idx

            if is_selected:
                cursor_line = line_counter
                g_sel = "class:msg.selected.gutter"
                glyph_sel = "\u2590 "  # ▐ — crimson gutter only; text keeps normal style
            else:
                g_sel = None
                glyph_sel = _BAR

            if msg.role == "user":
                g = g_sel or "class:msg.gutter.user"
                gg = glyph_sel
                for line in (msg.content.splitlines() or [""]):
                    for vline in _visual_lines(line, wrap_width):
                        fragments.append((g, gg))
                        fragments.append(("class:msg.user", vline + "\n"))
                        line_counter += 1
                fragments.append((g, gg + "\n"))
                fragments.append(("", "\n"))
                line_counter += 2
            elif msg.role == "agent":
                g = g_sel or "class:msg.gutter.agent"
                gg = glyph_sel
                for line in (msg.content.splitlines() or [""]):
                    for vline in _visual_lines(line, wrap_width):
                        fragments.append((g, gg))
                        fragments.extend(_render_inline(vline, "class:msg.agent", "class:msg.agent.bold"))
                        fragments.append(("class:msg.agent", "\n"))
                        line_counter += 1
                fragments.append((g, gg + "\n"))
                fragments.append(("", "\n"))
                line_counter += 2
            elif msg.role == "tool":
                style = "class:msg.tool.done" if msg.complete else "class:msg.tool"
                fragments.append((style, "  " + msg.content + "\n"))
                line_counter += 1

            # Inject inline detail below the selected message
            if is_selected:
                detail_frags = self._inline_detail(i, wrap_width)
                fragments.extend(detail_frags)
                line_counter += sum(f[1].count("\n") for f in detail_frags)

        if state.thinking:
            if self._streaming and self._streaming.content:
                for line in (self._streaming.content.splitlines() or [""]):
                    for vline in _visual_lines(line, wrap_width):
                        fragments.append(("class:msg.gutter.agent", _BAR))
                        fragments.extend(_render_inline(vline, "class:msg.agent", "class:msg.agent.bold"))
                        fragments.append(("class:msg.agent", "\n"))
                        line_counter += 1
                fragments.append(("class:msg.cursor", _CURSOR + "\n\n"))
                line_counter += 2
            else:
                spinner = _SPINNER_FRAMES[state.loader_frame % len(_SPINNER_FRAMES)]
                fragments.append(("class:msg.gutter.agent", _BAR))
                fragments.append(("class:msg.agent", spinner + "\n\n"))
                line_counter += 2

        self._line_count = line_counter
        if selected_idx >= 0:
            self._cursor_line = cursor_line
        elif hasattr(self, "_cursor_line"):
            del self._cursor_line
        return fragments
