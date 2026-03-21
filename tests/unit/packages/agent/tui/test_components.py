"""Unit tests for tui/components/ and tui/key_bindings.py."""

from __future__ import annotations

from unittest.mock import MagicMock

from agent.tui.components.history import HistoryControl
from agent.tui.components.status import StatusControl, _MCP_OK, _MCP_WAIT
from agent.tui.key_bindings import build_key_bindings
from agent.tui.state import Message, TuiState


# ---------------------------------------------------------------------------
# HistoryControl
# ---------------------------------------------------------------------------


class TestHistoryControl:
    def _text(self, state: TuiState) -> str:
        ctrl = HistoryControl(state)
        return "".join(text for _, text in ctrl._get_fragments())

    def test_empty_state_is_empty(self) -> None:
        assert self._text(TuiState()) == ""

    def test_user_message_rendered(self) -> None:
        state = TuiState(messages=[Message(role="user", content="ping", complete=True)])
        text = self._text(state)
        assert "((o))" in text
        assert "ping" in text

    def test_user_message_uses_custom_username(self) -> None:
        state = TuiState(username="Franco", messages=[Message(role="user", content="hi", complete=True)])
        text = self._text(state)
        assert "Franco" in text

    def test_agent_message_rendered(self) -> None:
        state = TuiState(messages=[Message(role="agent", content="pong", complete=True)])
        text = self._text(state)
        assert "))o((" in text
        assert "pong" in text

    def test_tool_message_rendered(self) -> None:
        state = TuiState(messages=[Message(role="tool", content="⚙ search…", complete=False)])
        text = self._text(state)
        assert "search" in text

    def test_thinking_shows_cursor(self) -> None:
        state = TuiState(thinking=True, current_agent_text="hel")
        text = self._text(state)
        assert "hel" in text
        assert "\u258b" in text  # cursor glyph

    def test_thinking_loader_frame_0_renders(self) -> None:
        # Frame 0: sin(0)=0, all signals in neutral zone — wave outputs spaces
        state = TuiState(thinking=True, current_agent_text="", loader_frame=0)
        text = self._text(state)
        assert text.strip() != ""  # some content is rendered

    def test_thinking_loader_frame_5_has_contracting_brackets(self) -> None:
        # Frame 5: sig ≈ 1.26, above threshold — wave contracts to "(( ))"
        state = TuiState(thinking=True, current_agent_text="", loader_frame=5)
        text = self._text(state)
        assert "((" in text



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
            on_cycle_panel=MagicMock(),
        )

    def test_quit_callback_registered(self) -> None:
        keys = [str(b.keys) for b in self._kb().bindings]
        assert any("c-x" in k for k in keys)

    def test_clear_callback_registered(self) -> None:
        keys = [str(b.keys) for b in self._kb().bindings]
        assert any("c-l" in k for k in keys)

    def test_toggle_logs_callback_registered(self) -> None:
        keys = [str(b.keys) for b in self._kb().bindings]
        assert any("c-p" in k for k in keys)

    def test_tab_cycle_binding_registered(self) -> None:
        # Tab is represented as c-i (Ctrl+I) in prompt_toolkit
        keys = [str(b.keys) for b in self._kb().bindings]
        assert any("c-i" in k for k in keys)
