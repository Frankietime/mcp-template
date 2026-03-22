"""Log line formatter — expands large JSON payloads for readability."""

from __future__ import annotations

import json

_INLINE_THRESHOLD = 120


def format_log_line(line: str) -> str:
    """Expand any JSON payload in *line* to multi-line for readability.

    Scans left-to-right for the first ``{`` or ``[``.  If the remainder
    parses as JSON and its compact form exceeds ``_INLINE_THRESHOLD`` chars,
    the payload is replaced with an indented multi-line block.
    Compact payloads and lines with no JSON are returned unchanged.
    """
    for i, ch in enumerate(line):
        if ch not in ("{", "["):
            continue
        try:
            parsed = json.loads(line[i:])
        except json.JSONDecodeError:
            continue
        compact = json.dumps(parsed)
        if len(compact) <= _INLINE_THRESHOLD:
            return line
        return line[:i] + "\n" + json.dumps(parsed, indent=2)
    return line
