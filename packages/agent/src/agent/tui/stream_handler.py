"""Bridges pydantic-ai event stream to TuiState mutations.

``make_stream_handler`` returns an ``EventStreamHandler`` compatible callable
that mutates *state* and calls ``app.invalidate()`` on each event so the
prompt_toolkit renderer repaints only the changed regions (differential rendering).
"""

from __future__ import annotations

from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any

from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
)

from .state import Message, TuiState

if TYPE_CHECKING:
    from prompt_toolkit import Application


def make_stream_handler(
    state: TuiState,
    app: Any,  # Application — typed as Any to avoid importing at module level
) -> Any:
    """Return an EventStreamHandler that streams agent output into *state*.

    Args:
        state: Shared TUI state; mutated in-place on each event.
        app: prompt_toolkit ``Application``; ``invalidate()`` is called after
            each mutation to schedule a differential repaint.

    Returns:
        An async callable matching the ``EventStreamHandler`` protocol.
    """

    async def handler(
        _ctx: Any,
        events: AsyncIterable[Any],
    ) -> None:
        async for event in events:
            if isinstance(event, PartStartEvent) and isinstance(event.part, TextPart):
                state.current_agent_text += event.part.content
                app.invalidate()

            elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                state.current_agent_text += event.delta.content_delta
                app.invalidate()

            elif isinstance(event, FunctionToolCallEvent):
                state.messages.append(
                    Message(
                        role="tool",
                        content=f"\u2699 {event.part.tool_name}\u2026",
                        complete=False,
                    )
                )
                app.invalidate()

            elif isinstance(event, FunctionToolResultEvent):
                for msg in reversed(state.messages):
                    if msg.role == "tool" and not msg.complete:
                        msg.complete = True
                        break
                app.invalidate()

    return handler
