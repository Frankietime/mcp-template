"""Unit tests for tui/components/ and tui/key_bindings.py."""

from __future__ import annotations

from unittest.mock import MagicMock

from tui.components.history import HistoryControl
from tui.components.status import StatusControl, _MCP_OK, _MCP_WAIT
from tui.key_bindings import build_key_bindings
from tui.state import TuiState


# ---------------------------------------------------------------------------
# HistoryControl
# ---------------------------------------------------------------------------


class TestHistoryControl:
    def _ctrl(self, state: TuiState | None = None) -> HistoryControl:
        return HistoryControl(state or TuiState())

    def _text(self, ctrl: HistoryControl) -> str:
        return "".join(text for _, text in ctrl._get_fragments())

    def test_empty_control_is_empty(self) -> None:
        assert self._text(self._ctrl()) == ""

    def test_user_message_rendered(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_user_message("ping")
        assert "ping" in self._text(ctrl)

    def test_agent_message_rendered(self) -> None:
        ctrl = self._ctrl()
        ctrl.start_agent_stream()
        ctrl.append_delta("pong")
        ctrl.end_agent_stream("pong")
        assert "pong" in self._text(ctrl)

    def test_agent_message_uses_agent_style(self) -> None:
        ctrl = self._ctrl()
        ctrl.start_agent_stream(agent_id="beetle")
        ctrl.end_agent_stream("hello")
        styles = [style for style, _ in ctrl._get_fragments()]
        assert any("msg.agent" in s for s in styles)

    def test_tool_message_rendered(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_tool_call("search")
        assert "search" in self._text(ctrl)

    def test_thinking_shows_loader_frame(self) -> None:
        state = TuiState(thinking=True, loader_frame=0)
        ctrl = HistoryControl(state)
        text = self._text(ctrl)
        assert text.strip() != ""  # some spinner content is rendered

    def test_thinking_with_streaming_shows_cursor(self) -> None:
        state = TuiState(thinking=True)
        ctrl = HistoryControl(state)
        ctrl.start_agent_stream()
        ctrl.append_delta("hel")
        text = self._text(ctrl)
        assert "hel" in text
        assert "\u258b" in text  # cursor glyph

    def test_clear_removes_messages(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_user_message("hi")
        ctrl.clear()
        assert self._text(ctrl) == ""

    def test_complete_last_tool_marks_complete(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_tool_call("search")
        assert ctrl._messages[0].complete is False
        ctrl.complete_last_tool()
        assert ctrl._messages[0].complete is True

    def test_end_agent_stream_with_no_delta_uses_final_output(self) -> None:
        ctrl = self._ctrl()
        ctrl.start_agent_stream()
        ctrl.end_agent_stream("direct output")
        assert "direct output" in self._text(ctrl)


# ---------------------------------------------------------------------------
# StatusControl
# ---------------------------------------------------------------------------


class TestStatusControl:
    def _text(self, state: TuiState) -> str:
        ctrl = StatusControl(state)
        return "".join(text for _, text in ctrl._get_fragments())

    def test_model_name_shown(self) -> None:
        state = TuiState(model_name="ollama:qwen3:4b")
        assert "ollama:qwen3:4b" in self._text(state)

    def test_mcp_connected_symbol(self) -> None:
        state = TuiState(mcp_connected=True)
        assert _MCP_OK in self._text(state)

    def test_mcp_disconnected_symbol(self) -> None:
        state = TuiState(mcp_connected=False)
        assert _MCP_WAIT in self._text(state)

    def test_thinking_indicator_shown(self) -> None:
        state = TuiState(thinking=True)
        assert "Thinking" in self._text(state)

    def test_thinking_indicator_hidden_when_not_thinking(self) -> None:
        state = TuiState(thinking=False)
        assert "Thinking" not in self._text(state)

    def test_spinner_advances(self) -> None:
        state = TuiState(thinking=True)
        ctrl = StatusControl(state)
        frame_before = ctrl._spinner_index
        ctrl.tick()
        assert ctrl._spinner_index == (frame_before + 1) % 10


# ---------------------------------------------------------------------------
# KeyBindings
# ---------------------------------------------------------------------------


class TestKeyBindings:
    def _kb(self):
        return build_key_bindings(
            on_quit=MagicMock(),
            on_clear=MagicMock(),
            on_toggle_logs=MagicMock(),
        )

    def test_quit_callback_registered(self) -> None:
        keys = [str(b.keys) for b in self._kb().bindings]
        assert any("c-x" in k for k in keys)

    def test_clear_callback_registered(self) -> None:
        keys = [str(b.keys) for b in self._kb().bindings]
        assert any("c-l" in k for k in keys)

    def test_tab_toggles_logs_binding_registered(self) -> None:
        # Tab is represented as c-i (Ctrl+I) in prompt_toolkit
        keys = [str(b.keys) for b in self._kb().bindings]
        assert any("c-i" in k for k in keys)
