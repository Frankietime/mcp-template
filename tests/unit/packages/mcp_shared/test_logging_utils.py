"""Unit tests for mcp_shared logging utilities."""

import time

import pytest
from mcp_shared.logging import record_tool_execution, track_tool_execution


class TestRecordToolExecution:
    def test_records_success(self) -> None:
        # Should not raise; just prints to console
        start = time.perf_counter()
        record_tool_execution("test_tool", start, success=True)

    def test_records_failure(self) -> None:
        start = time.perf_counter()
        record_tool_execution("test_tool", start, success=False, error_type="ToolError")


class TestTrackToolExecution:
    @pytest.mark.asyncio
    async def test_wraps_successful_function(self) -> None:
        calls = []

        async def my_tool() -> str:
            calls.append("called")
            return "result"

        wrapped = track_tool_execution(my_tool)
        result = await wrapped()
        assert result == "result"
        assert calls == ["called"]

    @pytest.mark.asyncio
    async def test_propagates_exception(self) -> None:
        async def failing_tool() -> None:
            raise ValueError("something went wrong")

        wrapped = track_tool_execution(failing_tool)
        with pytest.raises(ValueError, match="something went wrong"):
            await wrapped()

    @pytest.mark.asyncio
    async def test_preserves_function_name(self) -> None:
        async def my_named_tool() -> str:
            return "ok"

        wrapped = track_tool_execution(my_named_tool)
        assert wrapped.__name__ == "my_named_tool"
