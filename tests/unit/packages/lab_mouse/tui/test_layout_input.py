"""Unit tests for tui/components/input.py and tui/layout.py."""

from __future__ import annotations

from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.controls import BufferControl

from equator.components import ContextBarControl, HistoryControl, InputControl, LogsControl, ModelSelectorControl, StatusControl
from equator.layout import build_layout
from equator.state import TuiState


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
        logs = LogsControl(state.log_lines, "logs")
        internal_logs = LogsControl(state.internal_log_lines, "internal_logs")
        context_bar = ContextBarControl(state)
        model_selector = ModelSelectorControl(state)
        layout = build_layout(
            state=state,
            history=history,
            input_ctrl=input_ctrl,
            status=status,
            logs=logs,
            internal_logs=internal_logs,
            context_bar=context_bar,
            model_selector=model_selector,
        )
        return layout, input_ctrl

    def test_returns_layout_instance(self) -> None:
        layout, _ = self._make_layout()
        assert isinstance(layout, Layout)

    def test_focused_element_is_input_buffer(self) -> None:
        layout, input_ctrl = self._make_layout()
        assert layout.current_control is input_ctrl.buffer_control


class TestInputControlWithCompleter:
    def test_accepts_completer_parameter(self) -> None:
        from unittest.mock import MagicMock
        mock_completer = MagicMock()
        ctrl = InputControl(on_submit=lambda _: None, completer=mock_completer)
        assert ctrl.buffer.completer is mock_completer

    def test_defaults_to_no_completer(self) -> None:
        from prompt_toolkit.completion import DummyCompleter
        ctrl = InputControl(on_submit=lambda _: None)
        assert isinstance(ctrl.buffer.completer, DummyCompleter)

    def test_complete_while_typing_enabled(self) -> None:
        from unittest.mock import MagicMock
        ctrl = InputControl(on_submit=lambda _: None, completer=MagicMock())
        assert ctrl.buffer.complete_while_typing()


class TestBuildLayoutFloatContainer:
    def _make_layout(self) -> Layout:
        state = TuiState()
        history = HistoryControl(state)
        input_ctrl = InputControl(on_submit=lambda _: None)
        status = StatusControl(state)
        logs = LogsControl(state.log_lines, "logs")
        internal_logs = LogsControl(state.internal_log_lines, "internal_logs")
        context_bar = ContextBarControl(state)
        model_selector = ModelSelectorControl(state)
        return build_layout(
            state=state,
            history=history,
            input_ctrl=input_ctrl,
            status=status,
            logs=logs,
            internal_logs=internal_logs,
            context_bar=context_bar,
            model_selector=model_selector,
        )

    def test_layout_root_is_float_container(self) -> None:
        from prompt_toolkit.layout.containers import FloatContainer
        layout = self._make_layout()
        assert isinstance(layout.container, FloatContainer)

    def test_float_container_has_completions_menu(self) -> None:
        from prompt_toolkit.layout.containers import FloatContainer
        from prompt_toolkit.layout.menus import CompletionsMenu
        layout = self._make_layout()
        root = layout.container
        assert isinstance(root, FloatContainer)
        # Layout has 2 floats: completions menu + model selector
        assert len(root.floats) == 2
        assert isinstance(root.floats[0].content, CompletionsMenu)


class TestTitleFragments:
    def test_contains_agent_name(self) -> None:
        from equator.layout import _title_fragments
        from equator.state import TuiState
        state = TuiState(agent_name="beetle")
        text = "".join(t for _, t in _title_fragments(state))
        assert "beetle" in text

    def test_fallback_when_no_agent_name(self) -> None:
        from equator.layout import _title_fragments
        from equator.state import TuiState
        state = TuiState(agent_name="")
        text = "".join(t for _, t in _title_fragments(state))
        assert "agent" in text

    def test_line_characters_present(self) -> None:
        from equator.layout import _title_fragments
        from equator.state import TuiState
        state = TuiState(agent_name="test")
        text = "".join(t for _, t in _title_fragments(state))
        assert "\u2500" in text
