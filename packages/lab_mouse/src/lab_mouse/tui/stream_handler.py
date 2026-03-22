"""Pure mapping from pydantic-ai stream events to SessionEvents.

No state, no app reference — just a function that translates one event
type to another.  AgentSession calls this and emits the result.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
)

from equator.protocol import SessionEvent, TextDeltaEvent, ToolCallEvent, ToolResultEvent


def _extract_args(part: Any) -> dict:
    """Extract tool call arguments as a dict from a ToolCallPart."""
    try:
        args = part.args
        if isinstance(args, dict):
            return args
        if isinstance(args, str):
            return json.loads(args)
    except Exception:
        pass
    return {}


def _extract_result(part: Any) -> str:
    """Extract tool result content as a string from a ToolReturnPart."""
    try:
        content = part.content
        if isinstance(content, str):
            return content
        return json.dumps(content)
    except Exception:
        return ""


def map_pydantic_event(event: Any) -> SessionEvent | None:
    """Map a pydantic-ai stream event to a SessionEvent.

    Returns ``None`` for event types that have no TUI representation.
    """
    if isinstance(event, PartStartEvent) and isinstance(event.part, TextPart):
        return TextDeltaEvent(content=event.part.content)
    if isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
        return TextDeltaEvent(content=event.delta.content_delta)
    if isinstance(event, FunctionToolCallEvent):
        return ToolCallEvent(name=event.part.tool_name, args=_extract_args(event.part))
    if isinstance(event, FunctionToolResultEvent):
        return ToolResultEvent(result=_extract_result(event.part))
    return None
