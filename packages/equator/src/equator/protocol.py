"""SessionProtocol and the SessionEvent union.

These are the only types that cross the boundary between a Session
(owns agent state) and a TuiApp (owns render state).  Every change
visible to the TUI is expressed as a SessionEvent.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal, Protocol


@dataclass
class TextDeltaEvent:
    """Incremental text chunk from a streaming agent response."""

    agent_id: str = "main"
    content: str = ""


@dataclass
class ToolCallEvent:
    """A tool call was dispatched."""

    name: str = ""
    args: dict = field(default_factory=dict)


@dataclass
class ToolResultEvent:
    """The most recent pending tool call completed."""

    result: str = ""


@dataclass
class AgentStartEvent:
    """The agent has begun processing a prompt."""

    agent_id: str = "main"


@dataclass
class AgentEndEvent:
    """The agent has finished; output is the final text response."""

    output: str = ""
    agent_id: str = "main"


@dataclass
class TokenUsageEvent:
    """Updated token usage after a completed run."""

    total: int = 0


@dataclass
class ClearedEvent:
    """Conversation history was cleared."""


SessionEvent = (
    TextDeltaEvent
    | ToolCallEvent
    | ToolResultEvent
    | AgentStartEvent
    | AgentEndEvent
    | TokenUsageEvent
    | ClearedEvent
)

_Unsubscribe = Callable[[], None]


class SessionProtocol(Protocol):
    """Contract every session must satisfy for a TuiApp to subscribe."""

    def subscribe(self, listener: Callable[[SessionEvent], None]) -> _Unsubscribe:
        """Register *listener*; return a callable that unsubscribes it."""
        ...

    def clear(self) -> None:
        """Clear conversation history and emit ClearedEvent."""
        ...
