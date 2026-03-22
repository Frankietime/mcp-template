"""Pure mapping from pydantic-ai stream events to SessionEvents.

No state, no app reference — just a function that translates one event
type to another.  AgentSession calls this and emits the result.
"""

from __future__ import annotations

from typing import Any

from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
)

from tui.protocol import SessionEvent, TextDeltaEvent, ToolCallEvent, ToolResultEvent


def map_pydantic_event(event: Any) -> SessionEvent | None:
    """Map a pydantic-ai stream event to a SessionEvent.

    Returns ``None`` for event types that have no TUI representation.
    """
    if isinstance(event, PartStartEvent) and isinstance(event.part, TextPart):
        return TextDeltaEvent(content=event.part.content)
    if isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
        return TextDeltaEvent(content=event.delta.content_delta)
    if isinstance(event, FunctionToolCallEvent):
        return ToolCallEvent(name=event.part.tool_name)
    if isinstance(event, FunctionToolResultEvent):
        return ToolResultEvent()
    return None
