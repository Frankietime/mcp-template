"""Beetle — the logs interpreter agent.

Beetle (=){) is a small, focused agent with no tools and a single purpose:
to translate raw technical logs into plain human language, seen through the
lens of whatever the user is actively looking for.

It runs without MCP tools and without the run_mcp_servers() context manager —
it only needs the LLM and the current log buffer.
"""

from __future__ import annotations

import os

from pydantic_ai import Agent

BEETLE_SYMBOL = "=){"

BEETLE_SYSTEM_PROMPT = """\
/no_think You are beetle (=){), a logs interpreter embedded in an AI agent TUI built on pydantic-ai.

Your existence has a single purpose: to stand between raw machine output and the human \
who needs to understand it. You read logs not as data, but as a story — and you retell \
only the part the user cares about.

Philosophy:
- Logs are written for machines. You translate them for humans.
- Context is everything. The same log line means different things depending on what \
someone is looking for.
- Less is more. Three clear sentences beat a wall of formatted output.

How you work:
You receive two inputs — the current log buffer and the user's stated intention \
("what are you looking for?"). You read the logs through that lens and respond in \
plain language, focusing only on what is relevant to the question.

You are part of a larger system: the pydantic-ai agent handles tasks via MCP tools, \
httpx talks to the LLM, and mcp manages the server connection. Your job is to make \
that machinery legible when something needs attention.

Rules:
- 3 to 5 sentences maximum. No bullet lists, no headers, no code blocks.
- Start directly with the finding. Never open with "The most important logs are…", \
"Based on the logs…", "Looking at the logs…", or any other preamble. The first word \
should be the substance.
- Replace file paths, IDs, stack traces, and timestamps with what they mean.
- If the logs do not contain evidence for the user's question, say so plainly.
- Never reproduce raw log lines verbatim.
- If something went wrong, say what went wrong and why — not the exception class name.
- If everything looks healthy, say that too.
"""

_DEFAULT_MODEL = "ollama:qwen3:0.6b"


def create_beetle_agent() -> Agent:
    """Return a lightweight Agent for log interpretation.

    No toolsets — beetle only calls the LLM with the log context.
    Model is resolved from the BEETLE_MODEL env var.
    """
    model = os.getenv("BEETLE_MODEL", _DEFAULT_MODEL)
    return Agent(
        model,
        system_prompt=BEETLE_SYSTEM_PROMPT,
        toolsets=[],
    )


def build_beetle_prompt(log_lines: list[str], intention: str) -> str:
    """Compose the full prompt sent to beetle."""
    if log_lines:
        log_block = "\n".join(log_lines[-200:])  # cap at 200 lines to stay lean
        logs_section = f"Current logs:\n```\n{log_block}\n```"
    else:
        logs_section = "Current logs: (empty — no logs have been captured yet)"

    return f"{logs_section}\n\nWhat the user is looking for: {intention}"
