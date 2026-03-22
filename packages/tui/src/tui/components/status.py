"""Status bar control — single line footer showing model, MCP, and hints."""

from __future__ import annotations

from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.layout.controls import FormattedTextControl

from ..state import TuiState

_SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
_MCP_OK = "\u2713"   # ✓
_MCP_WAIT = "\u2026"  # …
_DOT_ON = "\u25cf"   # ● filled
_DOT_OFF = "\u25cb"  # ○ empty

_LEVEL_ORDER = ("DBG", "INF", "WRN", "ERR", "CRT")
_LEVEL_ACTIVE_STYLE: dict[str, str] = {
    "DBG": "ansibrightblack",
    "INF": "#4a9eff",
    "WRN": "#c8860a",
    "ERR": "#c0392b",
    "CRT": "bold #8b0000",
}
_LEVEL_OFF_STYLE = "#555566"


class StatusControl(FormattedTextControl):
    """Renders a single-line status bar."""

    def __init__(self, state: TuiState) -> None:
        self._state = state
        self._spinner_index = 0
        super().__init__(self._get_fragments)

    def tick(self) -> None:
        self._spinner_index = (self._spinner_index + 1) % len(_SPINNER_FRAMES)

    def _get_fragments(self) -> StyleAndTextTuples:
        state = self._state
        mcp_symbol = _MCP_OK if state.mcp_connected else _MCP_WAIT
        mcp_style = "class:status.mcp.ok" if state.mcp_connected else "class:status.mcp.wait"

        fragments: StyleAndTextTuples = [
            ("class:status.model", f" {state.model_name} "),
            ("", "| "),
            (mcp_style, f"MCP: {mcp_symbol} "),
            ("", "| "),
        ]

        if state.thinking:
            spinner = _SPINNER_FRAMES[self._spinner_index]
            fragments.append(("class:status.thinking", f"{spinner} Thinking\u2026 "))
            fragments.append(("", "| "))

        for lvl in _LEVEL_ORDER:
            if lvl in state.active_levels:
                fragments.append((_LEVEL_ACTIVE_STYLE[lvl], f"{_DOT_ON}{lvl} "))
            else:
                fragments.append((_LEVEL_OFF_STYLE, f"{_DOT_OFF}{lvl} "))
        fragments.append(("", "| "))

        return fragments
