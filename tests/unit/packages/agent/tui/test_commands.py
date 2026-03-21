"""Unit tests for tui/commands.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent.tui.commands import CommandRegistry, PREFIX
from agent.tui.state import Message, TuiState


def _app() -> MagicMock:
    app = MagicMock()
    app.invalidate = MagicMock()
    return app


def _registry():
    from agent.tui.commands import registry
    return registry


class TestIsCommand:
    def test_plain_text_is_not_command(self) -> None:
        assert _registry().is_command("hello world") is False

    def test_comma_mid_sentence_is_not_command(self) -> None:
        assert _registry().is_command("yes, I agree") is False

    def test_comma_digit_is_command(self) -> None:
        assert _registry().is_command(",1") is True

    def test_comma_word_is_command(self) -> None:
        assert _registry().is_command(",print") is True

    def test_comma_mixed_alphanumeric_is_command(self) -> None:
        assert _registry().is_command(",log2") is True

    def test_prefix_is_comma(self) -> None:
        assert PREFIX == ","


class TestHandle:
    def test_non_command_returns_false(self) -> None:
        assert _registry().handle("hello", TuiState(), _app()) is False

    def test_known_command_returns_true(self) -> None:
        assert _registry().handle(",1", TuiState(), _app()) is True

    def test_unknown_command_returns_true_and_warns(self) -> None:
        state = TuiState()
        _registry().handle(",9", state, _app())
        assert any("9" in line for line in state.log_lines)
        assert state.active_panel == "logs"


class TestBuiltinCommands:
    def test_1_opens_logs_when_main(self) -> None:
        state = TuiState()  # active_panel="main"
        _registry().handle(",1", state, _app())
        assert state.active_panel == "logs"

    def test_1_closes_logs_when_open(self) -> None:
        state = TuiState(active_panel="logs")
        _registry().handle(",1", state, _app())
        assert state.active_panel == "main"

    def test_3_populates_log_lines_and_opens_logs(self) -> None:
        state = TuiState()
        _registry().handle(",3", state, _app())
        assert any(",1" in line for line in state.log_lines)
        assert any("/interpret" in line for line in state.log_lines)
        assert state.active_panel == "logs"
