"""Beetle — the logs interpreter agent.

Beetle (=){) is a small, focused agent with no tools and a single purpose:
to translate raw technical logs into plain human language, seen through the
lens of whatever the user is actively looking for.

It runs without MCP tools and without the run_mcp_servers() context manager —
it only needs the LLM and the current log buffer.
"""

from __future__ import annotations

import os
from typing import Literal

from pydantic_ai import Agent

from .log_filter import filter_for_context

BEETLE_SYMBOL = "=){"

BEETLE_SYSTEM_PROMPT = """\
/no_think You are beetle (=){), a logs interpreter embedded in an AI agent TUI built on pydantic-ai.

Your existence has a single purpose: to stand between raw machine output and the human \
who needs to understand it. You read logs not as data, but as a narrative — and you retell \
only the part the user cares about.

Philosophy:
- Logs are written for machines. You translate them for humans.
- Context is everything. The same log line means different things depending on what someone is looking for.
- Less is more. One sharp chain beats a paragraph nobody reads.

How you work:
You receive two inputs — the current log buffer and the user's stated intention. \
You read the logs through that lens and respond in the format specified at the end of each prompt.

Scope boundary:
You interpret system behaviour — not content. When logs contain JSON payloads, \
API responses, tool results, or any domain data, you do not explain what that data means. \
You only answer: did the system succeed or fail, and why? \
"The tool returned a result" is enough. "The response contained neural network weights" is out of scope.

Formatting rules:
- No bullet lists, no headers, no code blocks, no prose paragraphs unless the mode says otherwise.
- Start directly with the finding. No preamble ("Based on the logs…", "Looking at…", etc.).
- Replace file paths, IDs, stack traces, and timestamps with what they mean.
- Never reproduce raw log lines verbatim.
- If something went wrong, say what and why — not the exception class name.
- If everything looks healthy, say that too.
- Wrap key terms in *asterisks* so they render bold: error codes, status codes, \
service names, operation names, and anything a human would scan for first. \
Examples: *401*, *timeout*, *POST /api/submit*, *connection refused*.
- Your response length and shape are determined by the mode instruction at the end of each prompt. \
Obey it strictly — treat every limit as a hard ceiling. Cut words, not meaning.
"""

_DEFAULT_MODEL = "ollama:phi4-mini:3.8b"


def create_beetle_agent() -> Agent:
    """Return a lightweight Agent for log interpretation.

    No toolsets — beetle only calls the LLM with the log context.
    Model is resolved from the BEETLE_MODEL env var.
    """
    os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("BEETLE_MODEL", _DEFAULT_MODEL)
    return Agent(
        model,
        system_prompt=BEETLE_SYSTEM_PROMPT,
        toolsets=[],
        model_settings={"temperature": 0},
    )


_MODE_INSTRUCTIONS: dict[str, str] = {
    "realtime": (
        "Respond in ONE sentence, max 15 words. No line breaks. "
        "Use *asterisks* only around the single most important term."
    ),
    "explain": (
        "Respond as a flow chain: *event* > *next event* > *outcome*. "
        "Each link is 2–5 words. Use *asterisks* on key terms (status codes, service names, operations). "
        "Separate links with  >  (space-arrow-space). No sentences, no punctuation except asterisks and arrows. "
        "If there is a clear error, make it the last link. "
        "Aim for 4–7 links. Never exceed the character limit."
    ),
}

MAX_CHARS: dict[str, int] = {
    "realtime": 120,
    "explain": 400,
}


def build_beetle_prompt(
    log_lines: list[str],
    intention: str,
    max_lines: int = 200,
    mode: Literal["realtime", "explain"] = "explain",
    filter_noise: bool = True,
    active_levels: set[str] | None = None,
) -> str:
    """Compose the full prompt sent to beetle.

    ``max_lines`` caps the log context sent to the model.  Use a small value
    (e.g. 30) for real-time auto-analysis where only recent events matter;
    keep the default 200 for focused user queries that need full context.

    ``mode`` controls response length:
    - ``"realtime"`` — one sentence, for automatic live-log annotations
    - ``"explain"``  — one paragraph (3–5 sentences), for explicit user queries

    ``active_levels`` restricts which log levels beetle sees (e.g. ``{"ERR", "DBG"}``).
    Traceback continuation lines (indented) always pass through regardless.
    Pass ``None`` to include all levels.

    ``filter_noise`` removes known-noise patterns after level filtering.
    Both filters run before slicing to ``max_lines`` so the context window
    is filled with signal, not raw lines.
    """
    working: list[str] = log_lines
    if active_levels is not None:
        working = [
            line for line in working
            if any(line.startswith(f"[{lvl}]") for lvl in active_levels)
            or line.startswith("  ")  # traceback continuation lines always pass
        ]
    if filter_noise:
        working = filter_for_context(working)

    if working:
        log_block = "\n".join(working[-max_lines:])
        logs_section = f"Current logs:\n```\n{log_block}\n```"
    else:
        logs_section = "Current logs: (empty — no logs match the current filters)"

    mode_instruction = _MODE_INSTRUCTIONS[mode]
    return f"{logs_section}\n\nWhat the user is looking for: {intention}\n\n{mode_instruction}"
