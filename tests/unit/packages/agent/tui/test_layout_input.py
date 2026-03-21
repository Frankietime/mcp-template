"""Unit tests for tui/components/input.py and tui/layout.py."""

from __future__ import annotations

from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.controls import BufferControl

from agent.tui.components import ContextBarControl, HistoryControl, InputControl, LogsControl, StatusControl
from agent.tui.layout import build_layout
from agent.tui.state import TuiState


class TestInputControl:
    def test_buffer_is_multiline(self) -> None:
        ctrl = InputControl(on_submit=lambda _: None)
        # prompt_toolkit multiline is a Filter — call it to evaluate
        assert ctrl.buffer.multiline()

    def test_buffer_control_is_buffer_control(self) -> None:
        ctrl = InputControl(on_submit=lambda _: None)
        assert isinstance(ctrl.buffer_control, BufferControl)

    def test_accept_calls_on_submit(self) -> None:
        received: list[str] = []
        ctrl = InputControl(on_submit=received.append)
        ctrl.buffer.set_document.__class__  # ensure buffer exists
        ctrl.buffer.insert_text("hello world")
        ctrl._accept(ctrl.buffer)
        assert received == ["hello world"]

    def test_accept_skips_whitespace_only(self) -> None:
        received: list[str] = []
        ctrl = InputControl(on_submit=received.append)
        ctrl.buffer.insert_text("   ")
        ctrl._accept(ctrl.buffer)
        assert received == []

    def test_accept_resets_buffer(self) -> None:
        ctrl = InputControl(on_submit=lambda _: None)
        ctrl.buffer.insert_text("hello")
        ctrl._accept(ctrl.buffer)
        assert ctrl.buffer.text == ""


class TestBuildLayout:
    def _make_layout(self) -> tuple[Layout, InputControl]:
        state = TuiState()
        history = HistoryControl(state)
        input_ctrl = InputControl(on_submit=lambda _: None)
        status = StatusControl(state)
        logs = LogsControl(state)
        context_bar = ContextBarControl(state)
        layout = build_layout(
            state=state,
            history=history,
            input_ctrl=input_ctrl,
            status=status,
            logs=logs,
            context_bar=context_bar,
        )
        return layout, input_ctrl

    def test_returns_layout_instance(self) -> None:
        layout, _ = self._make_layout()
        assert isinstance(layout, Layout)

    def test_focused_element_is_input_buffer(self) -> None:
        layout, input_ctrl = self._make_layout()
        assert layout.current_control is input_ctrl.buffer_control
