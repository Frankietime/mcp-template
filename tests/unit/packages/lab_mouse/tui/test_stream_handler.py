"""Unit tests for tui/stream_handler.py — pure event mapping function."""

from __future__ import annotations

import pytest
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    ToolCallPart,
    ToolReturnPart,
)

from lab_mouse.tui.stream_handler import map_pydantic_event
from tui.protocol import TextDeltaEvent, ToolCallEvent, ToolResultEvent


class TestMapPydanticEvent:
    def test_part_start_text_returns_text_delta(self) -> None:
        event = PartStartEvent(index=0, part=TextPart(content="hel"))
        result = map_pydantic_event(event)
        assert isinstance(result, TextDeltaEvent)
        assert result.content == "hel"

    def test_part_delta_text_returns_text_delta(self) -> None:
        event = PartDeltaEvent(index=0, delta=TextPartDelta(content_delta="lo"))
        result = map_pydantic_event(event)
        assert isinstance(result, TextDeltaEvent)
        assert result.content == "lo"

    def test_tool_call_event_returns_tool_call(self) -> None:
        part = ToolCallPart(tool_name="search", args={}, tool_call_id="tc1")
        event = FunctionToolCallEvent(part=part)
        result = map_pydantic_event(event)
        assert isinstance(result, ToolCallEvent)
        assert result.name == "search"

    def test_tool_result_event_returns_tool_result(self) -> None:
        return_part = ToolReturnPart(tool_name="search", content="ok", tool_call_id="tc1")
        event = FunctionToolResultEvent(result=return_part)
        result = map_pydantic_event(event)
        assert isinstance(result, ToolResultEvent)

    def test_unknown_event_returns_none(self) -> None:
        assert map_pydantic_event("not_an_event") is None
        assert map_pydantic_event(42) is None
        assert map_pydantic_event(None) is None
