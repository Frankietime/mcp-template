"""Detail panel — always-visible panel showing the selected message overview.

Normal mode: auto-follows latest message, shows turn summary.
Inspect mode: shows selected message or full tool call detail (args + result).
"""

from __future__ import annotations

import json

from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.layout.controls import FormattedTextControl

from .history import HistoryControl, MessageView


def _fmt_json(obj: dict | str, max_chars: int = 200) -> str:
    """Return a compact or indented JSON string truncated to *max_chars*."""
    if not obj:
        return "(none)"
    try:
        text = json.dumps(obj, indent=2) if isinstance(obj, dict) else str(obj)
    except Exception:
        text = str(obj)
    if len(text) > max_chars:
        text = text[:max_chars] + "…"
    return text


class DetailControl(FormattedTextControl):
    """Crimson detail panel — shows metadata about the selected message."""

    def __init__(self, history: HistoryControl) -> None:
        super().__init__(self._get_fragments, focusable=False)
        self._history = history

    def _get_fragments(self) -> StyleAndTextTuples:
        state = self._history._state

        # --- No messages yet ---
        if not self._history._messages and not self._history._streaming:
            return [("class:detail.empty", " no messages yet\n")]

        # --- Tool detail (inspect mode, tool selected) ---
        tool = self._history.selected_tool()
        if state.detail_mode and tool is not None:
            return self._render_tool(tool)

        # --- Message summary ---
        msg = self._history.selected_message()
        return self._render_summary(msg)

    def _render_summary(self, msg: MessageView | None) -> StyleAndTextTuples:
        if msg is None:
            return [("class:detail.empty", " —\n")]
        state = self._history._state
        frags: StyleAndTextTuples = []

        role_label = msg.role.upper()
        frags.append(("class:detail.header", f" {role_label}"))
        if msg.agent_id and msg.agent_id != "main":
            frags.append(("class:detail.header", f" · {msg.agent_id}"))
        frags.append(("class:detail.header", f" · {len(msg.content)} chars\n"))

        if msg.role == "tool":
            name = msg.content.lstrip("\u2699 ").rstrip("\u2026")
            status = "done" if msg.complete else "pending"
            frags += [
                ("class:detail.key", " Tool:   "),
                ("class:detail.val", name + "\n"),
                ("class:detail.key", " Status: "),
                ("class:detail.val", status + "\n"),
            ]
        else:
            tools = self._history._adjacent_tools(
                self._history._cursor_idx if self._history._cursor_idx >= 0
                else len(self._history._messages) - 1
            )
            if tools:
                done = sum(1 for t in tools if t.complete)
                frags.append(("class:detail.key", f" Tools: "))
                frags.append(("class:detail.val", f"{done}/{len(tools)} completed"))
                if state.detail_mode:
                    frags.append(("class:detail.hint", "  ← → to navigate"))
                frags.append(("class:detail.val", "\n"))
            # Preview first line of content
            preview = msg.content.splitlines()[0][:100] if msg.content else ""
            if preview:
                frags += [
                    ("class:detail.key", " Preview: "),
                    ("class:detail.val", preview + "\n"),
                ]

        if not state.detail_mode:
            frags.append(("class:detail.hint", " Ctrl+I  inspect\n"))

        return frags

    def _render_tool(self, tool: MessageView) -> StyleAndTextTuples:
        state = self._history._state
        tools = self._history._selected_turn_tools()
        n = len(tools)
        idx = state.detail_tool_idx
        name = tool.content.lstrip("\u2699 ").rstrip("\u2026")
        frags: StyleAndTextTuples = []

        # Header: TOOL 1/3 · name
        frags.append(("class:detail.header", f" TOOL {idx + 1}/{n} · {name}\n"))

        # Args
        frags.append(("class:detail.key", " Args:   "))
        args_text = _fmt_json(tool.tool_args)
        frags.append(("class:detail.val", args_text + "\n"))

        # Result
        frags.append(("class:detail.key", " Result: "))
        result_text = tool.tool_result[:200] + "…" if len(tool.tool_result) > 200 else (tool.tool_result or "(pending)")
        frags.append(("class:detail.val", result_text + "\n"))

        return frags
