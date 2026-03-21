"""Scrollable conversation history control."""

from __future__ import annotations

import random

from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.layout.controls import FormattedTextControl

from ..state import TuiState

_CURSOR = "\u258b"  # ▋ block cursor glyph shown while streaming

# Adjacency graph — each state may only transition to neighbours that differ
# by ±1 parenthesis (similar form, one step away).  The two "families"
# (inward: () side, outward: )( side) are cross-linked at both the 2-char
# and 4-char levels so the walk can migrate between them organically.
_GRAPH: dict[str, list[str]] = {
    "()"  : ["(()", "())", ")("],
    ")("  : [")((",  "))(", "()"],
    "(()" : ["()",  "(())"],
    "())" : ["()",  "(())"],
    ")((" : [")(", "))(("],
    "))(": [")(", "))(("],
    "(())": ["(()", "())", "))(("],
    "))((": [")((",  "))(", "(())"],
}

# Pre-generate a long random walk at import time so every session feels
# different while the per-frame lookup stays O(1).
def _make_walk(length: int = 6000) -> list[str]:
    state = "()"
    walk = [state]
    for _ in range(length - 1):
        state = random.choice(_GRAPH[state])
        walk.append(state)
    return walk

_WALK = _make_walk()
_WALK_LEN = len(_WALK)

# Each spinner tick advances 6 positions → effective frame rate ≈ 40 fps
_STEP = 1


class HistoryControl(FormattedTextControl):
    """Renders conversation messages as formatted text fragments.

    User messages appear in cyan bold, agent messages in green,
    and tool-call rows in dim yellow.  While ``state.thinking`` is
    True a braille spinner is shown; once streaming starts a live
    cursor glyph is appended to the in-progress text.
    """

    def __init__(self, state: TuiState) -> None:
        self._state = state
        super().__init__(self._get_fragments)

    def _get_fragments(self) -> StyleAndTextTuples:
        fragments: StyleAndTextTuples = []
        state = self._state

        for msg in state.messages:
            if msg.role == "user":
                fragments.append(("bold ansicyan", f"{state.username}\n"))
                fragments.append(("", msg.content + "\n\n"))
            elif msg.role == "agent":
                fragments.append(("bold ansigreen", "))((\n"))
                fragments.append(("", msg.content + "\n\n"))
            elif msg.role == "tool":
                style = "ansiyellow" if msg.complete else "italic ansiyellow"
                fragments.append((style, msg.content + "\n"))

        if state.thinking:
            if state.current_agent_text:
                fragments.append(("bold ansigreen", "))((\n"))
                fragments.append(("", state.current_agent_text))
                fragments.append(("ansicyan", _CURSOR + "\n\n"))
            else:
                frame = _WALK[(state.loader_frame * _STEP) % _WALK_LEN]
                fragments.append(("bold ansigreen", f"{frame}\n\n"))

        return fragments
