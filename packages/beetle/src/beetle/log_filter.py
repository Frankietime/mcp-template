"""Log signal/noise classifier for beetle.

Classifies formatted log lines (produced by _format_line in log_server.py /
log_handler.py) into "signal" and "noise", so the beetle agent receives only
actionable information.

All public functions are pure: no side effects, no I/O, trivially testable.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Types

NoiseRule = Callable[[str], bool]


@dataclass(frozen=True)
class NoiseRuleEntry:
    """A named, toggleable noise classification rule."""

    name: str
    rule: NoiseRule
    enabled: bool = True


# ---------------------------------------------------------------------------
# Internal helpers

_LINE_RE = re.compile(
    r"^\[(?P<prefix>DBG|INF|WRN|ERR|CRT)\]\s+(?P<logger>[^:]+):\s+(?P<body>.*)$"
)


def _parse(line: str) -> tuple[str, str, str] | None:
    """Return (prefix, logger, body) or None if line doesn't match the format."""
    m = _LINE_RE.match(line)
    if not m:
        return None
    return m.group("prefix"), m.group("logger"), m.group("body")


# ---------------------------------------------------------------------------
# Built-in noise rules

_HTTP_SUCCESS_RE = re.compile(r'"HTTP/[\d.]+ [23]\d{2}\b')
_CHATTY_LOGGERS = frozenset({"httpx", "httpcore", "asyncio", "hpack"})
_PAI_TELEMETRY_RE = re.compile(
    r"(Sending request to|Received response from|Request tokens:|Response tokens:)"
)
_MCP_LIFECYCLE_RE = re.compile(
    r"(Server initialized|Client connected|Ping|Pong|session opened|session closed cleanly)"
)
_TOOL_ACCOUNTING_RE = re.compile(r"(Running tool|Tool.*returned|tool_call_id)")


def _is_http_success(line: str) -> bool:
    """[INF] httpx: ... "HTTP/x.x 2xx/3xx ..." — successful HTTP responses."""
    parsed = _parse(line)
    if not parsed:
        return False
    prefix, logger, body = parsed
    return (
        prefix == "INF"
        and logger.split(".")[0] == "httpx"
        and bool(_HTTP_SUCCESS_RE.search(body))
    )


def _is_debug_noise(line: str) -> bool:
    """[DBG] lines from known chatty infrastructure loggers."""
    parsed = _parse(line)
    if not parsed:
        return False
    prefix, logger, _ = parsed
    return prefix == "DBG" and logger.split(".")[0] in _CHATTY_LOGGERS


def _is_pydantic_ai_telemetry(line: str) -> bool:
    """pydantic-ai internal request/response accounting lines."""
    parsed = _parse(line)
    if not parsed:
        return False
    _, _, body = parsed
    return bool(_PAI_TELEMETRY_RE.search(body))


def _is_mcp_lifecycle(line: str) -> bool:
    """Routine MCP connect/disconnect/ping messages (no error involved)."""
    parsed = _parse(line)
    if not parsed:
        return False
    prefix, logger, body = parsed
    return (
        prefix == "INF"
        and "mcp" in logger
        and bool(_MCP_LIFECYCLE_RE.search(body))
    )


def _is_tool_accounting(line: str) -> bool:
    """pydantic-ai tool dispatch housekeeping when no failure is indicated."""
    parsed = _parse(line)
    if not parsed:
        return False
    prefix, _, body = parsed
    return prefix == "DBG" and bool(_TOOL_ACCOUNTING_RE.search(body))


# ---------------------------------------------------------------------------
# Rule registry

_DEFAULT_RULES: list[NoiseRuleEntry] = [
    NoiseRuleEntry("http_success",          _is_http_success),
    NoiseRuleEntry("debug_noise",           _is_debug_noise),
    NoiseRuleEntry("pydantic_ai_telemetry", _is_pydantic_ai_telemetry),
    NoiseRuleEntry("mcp_lifecycle",         _is_mcp_lifecycle),
    NoiseRuleEntry("tool_accounting",       _is_tool_accounting),
]


# ---------------------------------------------------------------------------
# Public API

def is_noise(line: str, rules: list[NoiseRuleEntry] = _DEFAULT_RULES) -> bool:
    """Return True if *line* matches any enabled noise rule.

    Lines that do not parse as ``[PREFIX] logger: body`` format (e.g.,
    traceback continuation lines starting with two spaces) are treated as
    signal and always return False.
    """
    return any(entry.rule(line) for entry in rules if entry.enabled)


def filter_for_context(
    log_lines: list[str],
    rules: list[NoiseRuleEntry] = _DEFAULT_RULES,
) -> list[str]:
    """Return only the signal lines from *log_lines*, preserving order.

    Lines that do not match the standard format are kept unconditionally —
    they are typically traceback continuation lines belonging to an error.
    """
    return [line for line in log_lines if not is_noise(line, rules)]
