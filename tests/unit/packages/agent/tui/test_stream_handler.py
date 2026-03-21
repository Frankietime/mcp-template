"""Unit tests for tui/stream_handler.py.

Uses synthetic event sequences; no live MCP server or API key required.
"""

from __future__ import annotations

from collections.abc import AsyncIterable
from unittest.mock import MagicMock

import pytest
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    ToolCallPart,
)

from agent.tui.state import Message, TuiState
from agent.tui.stream_handler import make_stream_handler


async def _stream(events: list) -> AsyncIterable:
    for e in events:
        yield e


def _mock_app() -> MagicMock:
    app = MagicMock()
    app.invalidate = MagicMock()
    return app


class TestMakeStreamHandler:
    @pytest.mark.asyncio
    async def test_text_streaming_accumulates(self) -> None:
        state = TuiState()
        app = _mock_app()
        handler = make_stream_handler(state, app)

        events = [
            PartStartEvent(index=0, part=TextPart(content="hel")),
            PartDeltaEvent(index=0, delta=TextPartDelta(content_delta="lo")),
            PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=" world")),
        ]
        await handler(None, _stream(events))

        assert state.current_agent_text == "hello world"
        assert app.invalidate.call_count == 3

    @pytest.mark.asyncio
    async def test_part_start_appends_to_current_text(self) -> None:
        # Multiple TextPart events (e.g. thinking block + response) must accumulate,
        # not overwrite — otherwise only the last part would be shown.
        state = TuiState(current_agent_text="first ")
        app = _mock_app()
        handler = make_stream_handler(state, app)

        await handler(None, _stream([PartStartEvent(index=0, part=TextPart(content="second"))]))

        assert state.current_agent_text == "first second"

    @pytest.mark.asyncio
    async def test_tool_call_appends_message(self) -> None:
        state = TuiState()
        app = _mock_app()
        handler = make_stream_handler(state, app)

        tool_part = ToolCallPart(tool_name="search", args={}, tool_call_id="tc1")
        await handler(None, _stream([FunctionToolCallEvent(part=tool_part)]))

        assert len(state.messages) == 1
        assert state.messages[0].role == "tool"
        assert "search" in state.messages[0].content
        assert state.messages[0].complete is False

    @pytest.mark.asyncio
    async def test_tool_result_marks_complete(self) -> None:
        state = TuiState()
        state.messages.append(Message(role="tool", content="⚙ search…", complete=False))
        app = _mock_app()
        handler = make_stream_handler(state, app)

        from pydantic_ai.messages import ToolReturnPart
        return_part = ToolReturnPart(tool_name="search", content="result", tool_call_id="tc1")
        await handler(None, _stream([FunctionToolResultEvent(result=return_part)]))

        assert state.messages[0].complete is True

    @pytest.mark.asyncio
    async def test_tool_result_only_marks_last_incomplete(self) -> None:
        state = TuiState()
        state.messages.append(Message(role="tool", content="⚙ a…", complete=True))
        state.messages.append(Message(role="tool", content="⚙ b…", complete=False))
        app = _mock_app()
        handler = make_stream_handler(state, app)

        from pydantic_ai.messages import ToolReturnPart
        return_part = ToolReturnPart(tool_name="b", content="ok", tool_call_id="tc2")
        await handler(None, _stream([FunctionToolResultEvent(result=return_part)]))

        assert state.messages[0].complete is True   # unchanged
        assert state.messages[1].complete is True   # newly completed

    @pytest.mark.asyncio
    async def test_unknown_events_are_ignored(self) -> None:
        state = TuiState()
        app = _mock_app()
        handler = make_stream_handler(state, app)

        await handler(None, _stream(["not_an_event", 42, None]))

        assert state.messages == []
        assert state.current_agent_text == ""
        assert app.invalidate.call_count == 0
