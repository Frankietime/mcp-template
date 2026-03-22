"""BeetleSession — minimal session for the beetle log-interpreter agent.

No MCP, no tools, no streaming — just a single agent.run() per prompt.
"""

from __future__ import annotations

from collections.abc import Callable

from tui.protocol import (
    AgentEndEvent,
    AgentStartEvent,
    ClearedEvent,
    SessionEvent,
    TextDeltaEvent,
)

from .agent import build_beetle_prompt, create_beetle_agent


class BeetleSession:
    """Satisfies SessionProtocol for the beetle chatbot TUI."""

    def __init__(self, log_lines: list[str]) -> None:
        self._log_lines = log_lines
        self._agent = create_beetle_agent()
        self._listeners: list[Callable[[SessionEvent], None]] = []

    # ------------------------------------------------------------------
    # SessionProtocol

    def subscribe(self, listener: Callable[[SessionEvent], None]) -> Callable[[], None]:
        """Register *listener*; return a callable that removes it."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    def clear(self) -> None:
        """Notify subscribers that history was cleared (beetle is stateless)."""
        self._emit(ClearedEvent())

    # ------------------------------------------------------------------
    # Log buffer

    def append_line(self, line: str) -> None:
        """Append a live log line and keep the buffer bounded to 1 000 lines."""
        self._log_lines.append(line)
        if len(self._log_lines) > 1_000:
            del self._log_lines[:-1_000]

    # ------------------------------------------------------------------
    # Agent interaction

    async def prompt(
        self,
        text: str,
        max_lines: int = 200,
        mode: str = "explain",
        active_levels: set[str] | None = None,
    ) -> None:
        """Stream *text* through beetle, emitting token deltas as they arrive.

        ``mode`` controls response length — "realtime" (120 chars) or "explain"
        (500 chars).  Truncation is enforced in the stream loop regardless of
        what the model produces.

        ``active_levels`` restricts which log levels are included in the agent
        context (e.g. ``{"ERR", "DBG"}``).  Pass ``None`` to include all levels.
        """
        self._emit(AgentStartEvent(agent_id="beetle"))
        try:
            beetle_prompt = build_beetle_prompt(
                self._log_lines, text, max_lines=max_lines, mode=mode,
                active_levels=active_levels,
            )
            async with self._agent.run_stream(beetle_prompt) as result:
                async for delta in result.stream_text(delta=True):
                    self._emit(TextDeltaEvent(agent_id="beetle", content=delta))
            self._emit(AgentEndEvent(output="", agent_id="beetle"))
        except Exception as e:  # noqa: BLE001
            self._emit(AgentEndEvent(output=f"[error] {e}", agent_id="beetle"))

    # ------------------------------------------------------------------
    # Internal

    def _emit(self, event: SessionEvent) -> None:
        for listener in list(self._listeners):
            listener(event)
