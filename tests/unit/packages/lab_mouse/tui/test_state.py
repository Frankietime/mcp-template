"""Unit tests for tui/state.py."""

from tui.state import TuiState


class TestTuiState:
    def test_defaults(self) -> None:
        state = TuiState()
        assert state.thinking is False
        assert state.mcp_connected is False
        assert state.model_name == ""
        assert state.username == "((o))"
        assert state.loader_frame == 0
        assert state.log_lines == []
        assert state.active_panel == "main"
        assert state.context_tokens_used == 0
        assert state.context_tokens_max == 32_768

    def test_thinking_toggle(self) -> None:
        state = TuiState()
        state.thinking = True
        assert state.thinking is True
        state.thinking = False
        assert state.thinking is False

    def test_mcp_connected(self) -> None:
        state = TuiState()
        state.mcp_connected = True
        assert state.mcp_connected is True

    def test_log_lines_append(self) -> None:
        state = TuiState()
        state.log_lines.append("[INF] test: hello")
        assert len(state.log_lines) == 1
