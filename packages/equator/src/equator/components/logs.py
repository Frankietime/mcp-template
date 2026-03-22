"""Raw log panel — paginated view of pydantic_ai / httpx / mcp log lines.

Toggled by Tab.  Left/right arrows page through log history.

Uses FormattedTextControl (read-only) so left/right keys are NOT consumed
by a Buffer's cursor-movement bindings — they fall through to the global
page-navigation bindings in key_bindings.py.
"""

from __future__ import annotations

import re

from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension


_PAGE_SIZE = 15  # log lines shown per page

_LEVEL_STYLE = {
    "DBG": "class:log.dbg",
    "INF": "class:log.inf",
    "WRN": "class:log.wrn",
    "ERR": "class:log.err",
    "CRT": "class:log.crt",
}

_JSON_FRAGMENT_RE = re.compile(
    r'(?P<key>"[\w\- ]+"\s*:)|(?P<str>"[^"]*")|(?P<num>\b[\d.]+\b)|(?P<kw>true|false|null)'
)


def _lex_json_line(line: str) -> StyleAndTextTuples:
    frags: StyleAndTextTuples = []
    last = 0
    for m in _JSON_FRAGMENT_RE.finditer(line):
        if m.start() > last:
            frags.append(("class:log.json", line[last:m.start()]))
        if m.lastgroup == "key":
            frags.append(("class:log.json.key", m.group()))
        else:
            frags.append(("class:log.json.val", m.group()))
        last = m.end()
    if last < len(line):
        frags.append(("class:log.json", line[last:]))
    return frags or [("class:log.json", line)]


def _color_line(line: str) -> StyleAndTextTuples:
    """Apply log-level or JSON colouring to a single log line."""
    if line.startswith("[") and "]" in line:
        close = line.index("]") + 1
        tag = line[1: close - 1]
        style = _LEVEL_STYLE.get(tag, "")
        if style:
            return [(style, line[:close]), ("", line[close:])]
    if line.startswith(" ") or line.startswith("{") or line.startswith("["):
        return _lex_json_line(line)
    return [("", line)]


class LogsControl:
    """Paginated read-only log panel.

    Left arrow pages toward older logs, right arrow toward newer.
    Auto-follows new entries when the user is already on the last page.
    """

    def __init__(self, log_lines: list[str], name: str = "logs") -> None:
        self._log_lines = log_lines
        self._page: int = 0          # 0-indexed from oldest; last page = most recent
        self._at_last_page: bool = True

        self.container = HSplit([
            Window(
                content=FormattedTextControl(self._page_fragments),
                height=Dimension(min=3, weight=1),
                wrap_lines=True,
            ),
            Window(
                content=FormattedTextControl(self._indicator_fragments),
                height=1,
                char="\u2500",  # ─ fills the row; indicator text overlays from the left
            ),
        ])

    # ------------------------------------------------------------------
    # Navigation

    def page_back(self) -> None:
        """Show the previous (older) page."""
        if self._page > 0:
            self._page -= 1
            self._at_last_page = False

    def page_forward(self) -> None:
        """Show the next (newer) page."""
        tp = self._total_pages()
        if self._page < tp - 1:
            self._page += 1
        if self._page >= tp - 1:
            self._at_last_page = True

    # ------------------------------------------------------------------
    # Public

    def refresh(self) -> None:
        """Update the page index when new log lines arrive.

        If the user was already on the last page, follow the new content.
        Otherwise keep their current position.  The FormattedTextControl
        re-reads _log_lines on the next render automatically.
        """
        tp = self._total_pages()
        if self._at_last_page:
            self._page = max(0, tp - 1)
        else:
            self._page = max(0, min(self._page, tp - 1))

    # ------------------------------------------------------------------
    # Rendering

    def _total_pages(self) -> int:
        return max(1, (len(self._log_lines) + _PAGE_SIZE - 1) // _PAGE_SIZE)

    def _page_lines(self) -> list[str]:
        start = self._page * _PAGE_SIZE
        end = min(start + _PAGE_SIZE, len(self._log_lines))
        return self._log_lines[start:end]

    def _page_fragments(self) -> StyleAndTextTuples:
        fragments: StyleAndTextTuples = []
        for line in self._page_lines():
            fragments.extend(_color_line(line))
            fragments.append(("", "\n"))
        return fragments

    def _indicator_fragments(self) -> StyleAndTextTuples:
        """Page indicator overlaid on the ─ separator row."""
        tp = self._total_pages()
        current = self._page + 1  # 1-indexed for display
        suffix = " end" if self._page >= tp - 1 else ""
        return [("class:logs.page", f" ← {current}/{tp}{suffix} → ")]
