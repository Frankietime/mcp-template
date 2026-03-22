"""HelpControl — left-sidebar key-binding reference panel."""

from __future__ import annotations

from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.layout.controls import FormattedTextControl

from ..state import TuiState

_BINDINGS: list[tuple[str, str]] = [
    ("Ctrl+O",  "toggle logs"),
    ("Tab",     "toggle help"),
    ("F2",      "inspect expand"),
    ("Ctrl+X",  "quit"),
    ("",        ""),
    ("↑ ↓",    "navigate msgs"),
    ("← →",    "cycle tool calls"),
    ("Esc",     "clear cursor"),
    ("",        ""),
    ("/help",   "commands & keys"),
    ("/logs",   "filter log levels"),
    ("/model",  "change model"),
    ("/q",      "quit"),
]


class HelpControl(FormattedTextControl):
    """Renders a compact key-binding reference as a left sidebar."""

    def __init__(self, state: TuiState) -> None:
        self._state = state
        super().__init__(self._get_fragments)

    def _get_fragments(self) -> StyleAndTextTuples:
        frags: StyleAndTextTuples = []
        frags.append(("class:help.header", " Keys\n"))
        frags.append(("class:help.sep", " " + "\u2500" * 22 + "\n"))
        for key, desc in _BINDINGS:
            if not key and not desc:
                frags.append(("", "\n"))
                continue
            frags.append(("class:help.key", f" {key:<8}"))
            frags.append(("class:help.text", f" {desc}\n"))
        frags.append(("class:help.sep", " " + "\u2500" * 22 + "\n"))
        return frags
