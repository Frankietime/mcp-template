"""Raw log panel — scrollable view of pydantic_ai / httpx / mcp log lines.

Toggled by ``,1``.  Arrow keys scroll the buffer.
"""

from __future__ import annotations

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.lexers import Lexer

from ..state import TuiState

_LEVEL_STYLE = {
    "DBG": "class:log.dbg",
    "INF": "class:log.inf",
    "WRN": "class:log.wrn",
    "ERR": "class:log.err",
    "CRT": "class:log.crt",
}


class _LogLexer(Lexer):
    """Colours the [LEVEL] prefix tag; leaves the rest of the line unstyled."""

    def lex_document(self, document: Document):
        lines = document.lines

        def get_line(lineno: int):
            if lineno >= len(lines):
                return []
            line = lines[lineno]
            if line.startswith("[") and "]" in line:
                close = line.index("]") + 1
                tag = line[1: close - 1]
                style = _LEVEL_STYLE.get(tag, "")
                if style:
                    return [(style, line[:close]), ("", line[close:])]
            return [("", line)]

        return get_line


class LogsControl:
    """Scrollable raw-log panel."""

    def __init__(self, state: TuiState) -> None:
        self._state = state
        self.buffer = Buffer(multiline=True, name="logs")
        self.buffer_control = BufferControl(
            buffer=self.buffer,
            focusable=True,
            lexer=_LogLexer(),
        )
        self.container = HSplit([
            Window(
                content=self.buffer_control,
                height=Dimension(min=3, weight=1),
                wrap_lines=True,
                allow_scroll_beyond_bottom=True,
            ),
            Window(height=1, char="\u2500"),
        ])

    def refresh(self) -> None:
        """Sync the buffer with the current ``state.log_lines``."""
        text = "\n".join(self._state.log_lines)
        self.buffer.set_document(Document(text=text, cursor_position=len(text)))
