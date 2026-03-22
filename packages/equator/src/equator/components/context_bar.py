"""Context window progress bar — single footer row showing token usage."""

from __future__ import annotations

from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl

from ..state import TuiState

_BAR_WIDTH = 20
_FILL = "\u2588"   # █
_EMPTY = "\u2591"  # ░


def _bar_style(pct: float) -> str:
    if pct >= 0.9:
        return "class:ctx.high"
    if pct >= 0.7:
        return "class:ctx.mid"
    return "class:ctx.low"


class ContextBarControl:
    """Single-row token-usage progress bar rendered at the bottom of the TUI."""

    def __init__(self, state: TuiState) -> None:
        self._state = state
        self.container = Window(
            content=FormattedTextControl(self._get_fragments),
            height=1,
        )

    def _get_fragments(self) -> StyleAndTextTuples:
        used = self._state.context_tokens_used
        max_ = self._state.context_tokens_max
        pct = used / max_ if max_ > 0 else 0.0
        filled = round(pct * _BAR_WIDTH)
        bar = _FILL * filled + _EMPTY * (_BAR_WIDTH - filled)
        style = _bar_style(pct)
        pct_label = f"{pct:.0%}"
        return [
            ("", "Context  "),
            (style, bar),
            ("", f"  {used:,} / {max_:,}  ({pct_label})"),
        ]
