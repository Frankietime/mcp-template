"""JSON syntax lexer for the detail / inspector panel.

Returns ``StyleAndTextTuples`` using ``detail.json.*`` CSS classes so the
inspector can be themed independently from the log panel (``log.json.*``).

Usage::

    from ._json_lex import lex_json_fragments

    frags += lex_json_fragments(tool.tool_args)   # dict → pretty-printed + lexed
    frags += lex_json_fragments(tool.tool_result)  # str → try JSON parse, else plain
"""

from __future__ import annotations

import json
import re

from prompt_toolkit.formatted_text import StyleAndTextTuples

# ---------------------------------------------------------------------------
# Token regex — applied per line after json.dumps(indent=2)
# ---------------------------------------------------------------------------

_JSON_RE = re.compile(
    r'(?P<key>"(?:[^"\\]|\\.)*"\s*:)'                       # "key":
    r'|(?P<str>"(?:[^"\\]|\\.)*")'                          # "string value"
    r'|(?P<num>-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b)'      # integer / float
    r'|(?P<kw>\btrue\b|\bfalse\b|\bnull\b)',                 # keyword
)

_STYLE_MAP: dict[str, str] = {
    "key": "class:detail.json.key",
    "str": "class:detail.json.str",
    "num": "class:detail.json.num",
    "kw":  "class:detail.json.kw",
}


def _lex_line(line: str) -> StyleAndTextTuples:
    """Tokenise a single JSON line into styled fragments."""
    frags: StyleAndTextTuples = []
    last = 0
    for m in _JSON_RE.finditer(line):
        if m.start() > last:
            frags.append(("class:detail.json", line[last:m.start()]))
        frags.append((_STYLE_MAP[m.lastgroup], m.group()))  # type: ignore[index]
        last = m.end()
    if last < len(line):
        frags.append(("class:detail.json", line[last:]))
    return frags or [("class:detail.json", line)]


def lex_json_fragments(obj: dict | str) -> StyleAndTextTuples:
    """Return syntax-highlighted fragments for *obj*.

    - ``dict``  → pretty-printed with ``indent=2`` then lexed.
    - ``str``   → attempted ``json.loads``; if valid, pretty-prints then lexes;
                  otherwise renders as plain ``detail.val`` text.
    - Falsy     → returns a single ``detail.empty`` placeholder fragment.
    """
    if not obj:
        return [("class:detail.empty", "(none)\n")]

    if isinstance(obj, dict):
        try:
            text = json.dumps(obj, indent=2)
        except Exception:
            text = str(obj)
    else:
        try:
            parsed = json.loads(obj)
            text = json.dumps(parsed, indent=2)
        except (json.JSONDecodeError, TypeError, ValueError):
            # Plain text — not JSON
            return [("class:detail.val", obj + "\n")]

    frags: StyleAndTextTuples = []
    for line in text.splitlines():
        frags.extend(_lex_line(line))
        frags.append(("", "\n"))
    return frags
