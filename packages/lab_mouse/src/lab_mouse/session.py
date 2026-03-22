"""AgentSession — owns all agent state and emits SessionEvents to the TUI.

Single writer rule: nothing outside AgentSession writes to _pydantic_messages.
The TUI subscribes and reacts to events; it never accesses agent internals.
"""

from __future__ import annotations

from collections.abc import AsyncIterable, Callable
from typing import Any

from equator.protocol import (
    AgentEndEvent,
    AgentStartEvent,
    ClearedEvent,
    SessionEvent,
    TokenUsageEvent,
)

from .agent import create_agent
from .deps import AgentDeps
from .tui.stream_handler import map_pydantic_event


class AgentSession:
    """Owns the pydantic-ai agent and its conversation history.

    Usage::

        async with AgentSession(deps) as session:
            unsubscribe = session.subscribe(my_listener)
            await session.prompt("Hello")
            unsubscribe()
    """

    def __init__(self, deps: AgentDeps) -> None:
        self._deps = deps
        self._agent = create_agent(deps)
        self._pydantic_messages: list = []
        self._listeners: list[Callable[[SessionEvent], None]] = []
        self._mcp_cm: Any = None

    # ------------------------------------------------------------------
    # Async context manager — manages MCP server lifetime

    async def __aenter__(self) -> AgentSession:
        self._mcp_cm = self._agent.run_mcp_servers()
        await self._mcp_cm.__aenter__()
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._mcp_cm is not None:
            await self._mcp_cm.__aexit__(*args)

    # ------------------------------------------------------------------
    # SessionProtocol

    def subscribe(self, listener: Callable[[SessionEvent], None]) -> Callable[[], None]:
        """Register *listener*; return a callable that removes it."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    def clear(self) -> None:
        """Clear conversation history atomically and notify subscribers."""
        self._pydantic_messages.clear()
        self._emit(ClearedEvent())

    # ------------------------------------------------------------------
    # Agent interaction

    async def prompt(self, text: str) -> None:
        """Run *text* through the agent and emit events as they arrive."""
        self._emit(AgentStartEvent())

        async def _event_handler(_ctx: Any, events: AsyncIterable[Any]) -> None:
            async for event in events:
                mapped = map_pydantic_event(event)
                if mapped is not None:
                    self._emit(mapped)

        usage: Any = None
        result_output: str = ""
        try:
            async with self._agent.run_stream(
                text,
                deps=self._deps,
                message_history=self._pydantic_messages,
                model=self._deps.model,
                model_settings={"temperature": 0.1},
                event_stream_handler=_event_handler,
            ) as streamed:
                result = await streamed.get_output()
                if isinstance(result, str):
                    result_output = result
                # Must be inside async with — stream closes on __aexit__
                self._pydantic_messages = list(streamed.all_messages())
                usage = streamed.usage()
        except Exception as e:  # noqa: BLE001
            self._emit(AgentEndEvent(output=f"[error] {e}"))
            return

        self._emit(AgentEndEvent(output=result_output))
        if usage is not None and usage.total_tokens:
            self._emit(TokenUsageEvent(total=usage.total_tokens))

    # ------------------------------------------------------------------
    # Internal

    def _emit(self, event: SessionEvent) -> None:
        for listener in list(self._listeners):
            listener(event)
