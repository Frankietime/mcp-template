"""Status bar control — single line footer showing model, MCP, and hints."""

from __future__ import annotations

from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.layout.controls import FormattedTextControl

from ..state import TuiState

_SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
_MCP_OK = "\u2713"   # ✓
_MCP_WAIT = "\u2026"  # …


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
        mcp_style = "ansigreen" if state.mcp_connected else "ansiyellow"

        fragments: StyleAndTextTuples = [
            ("bold", f" {state.model_name} "),
            ("", "| "),
            (mcp_style, f"MCP: {mcp_symbol} "),
            ("", "| "),
        ]

        if state.thinking:
            spinner = _SPINNER_FRAMES[self._spinner_index]
            fragments.append(("italic ansiyellow", f"{spinner} Thinking\u2026 "))
            fragments.append(("", "| "))

        if state.active_panel == "logs":
            fragments += [
                ("ansibrightblack", "Tab cycle  ,1 close  ,3 help  Ctrl+X quit"),
            ]
        else:
            fragments += [
                ("ansibrightblack", "Enter send  Tab cycle  Esc+Enter newline  ,3 help  Ctrl+X quit"),
            ]
        return fragments
