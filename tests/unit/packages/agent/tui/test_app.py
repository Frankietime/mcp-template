"""Unit tests for TuiApp internals (no live MCP/API required)."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from agent.deps import AgentDeps
from agent.tui.app import TuiApp
from agent.tui.state import Message


def _make_app() -> TuiApp:
    deps = AgentDeps(model="test-model")
    # Patch Application so no real terminal is required
    with patch("agent.tui.app.Application") as MockApp:
        MockApp.return_value = MagicMock()
        app = TuiApp(deps)
    return app


class TestTuiAppInit:
    def test_state_model_name_matches_deps(self) -> None:
        app = _make_app()
        assert app._state.model_name == "test-model"

    def test_state_starts_not_thinking(self) -> None:
        app = _make_app()
        assert app._state.thinking is False

    def test_state_starts_mcp_disconnected(self) -> None:
        app = _make_app()
        assert app._state.mcp_connected is False

    def test_queues_are_empty(self) -> None:
        app = _make_app()
        assert app._cmd_queue.empty()
        assert app._msg_queue.empty()


class TestTuiAppHandlers:
    def test_handle_clear_empties_messages(self) -> None:
        app = _make_app()
        app._state.messages.append(Message(role="user", content="hi", complete=True))
        app._state.current_agent_text = "partial"
        app._handle_clear()
        assert app._state.messages == []
        assert app._state.current_agent_text == ""

    def test_handle_clear_calls_invalidate(self) -> None:
        app = _make_app()
        app._handle_clear()
        app._app.invalidate.assert_called()

    def test_handle_quit_calls_exit(self) -> None:
        app = _make_app()
        app._handle_quit()
        app._app.exit.assert_called_once()


class TestRouteInput:
    def test_command_goes_to_cmd_queue(self) -> None:
        app = _make_app()
        app._route_input(",1")
        assert not app._cmd_queue.empty()
        assert app._msg_queue.empty()

    def test_message_goes_to_msg_queue(self) -> None:
        app = _make_app()
        app._route_input("hello agent")
        assert app._cmd_queue.empty()
        assert not app._msg_queue.empty()

    def test_interpret_calls_launch_beetle(self) -> None:
        app = _make_app()
        with patch.object(app, "_launch_beetle") as mock_launch:
            app._route_input("/interpret")
            mock_launch.assert_called_once()

    def test_interpret_does_not_enqueue_to_msg_or_cmd(self) -> None:
        app = _make_app()
        with patch.object(app, "_launch_beetle"):
            app._route_input("/interpret")
        assert app._cmd_queue.empty()
        assert app._msg_queue.empty()


class TestSetPanel:
    def test_set_panel_updates_active_panel(self) -> None:
        app = _make_app()
        app._set_panel("logs")
        assert app._state.active_panel == "logs"

    def test_set_panel_back_to_main(self) -> None:
        app = _make_app()
        app._set_panel("logs")
        app._set_panel("main")
        assert app._state.active_panel == "main"

    def test_set_panel_calls_invalidate(self) -> None:
        app = _make_app()
        app._set_panel("logs")
        app._app.invalidate.assert_called()


class TestCyclePanel:
    def test_cycles_main_to_logs(self) -> None:
        app = _make_app()
        assert app._state.active_panel == "main"
        app._cycle_panel()
        assert app._state.active_panel == "logs"

    def test_cycles_logs_back_to_main(self) -> None:
        app = _make_app()
        app._state.active_panel = "logs"
        app._cycle_panel()
        assert app._state.active_panel == "main"

    def test_full_cycle_returns_to_start(self) -> None:
        app = _make_app()
        for _ in range(2):
            app._cycle_panel()
        assert app._state.active_panel == "main"


class TestLaunchBeetle:
    def test_launch_writes_logs_to_tempfile_and_spawns_process(self) -> None:
        app = _make_app()
        app._state.log_lines = ["[INF] agent: hello", "[ERR] agent: boom"]
        with patch("agent.tui.app.subprocess.Popen") as mock_popen, \
             patch("agent.tui.app.tempfile.NamedTemporaryFile") as mock_tf:
            mock_file = MagicMock()
            mock_file.name = "/tmp/test.log"
            mock_tf.return_value.__enter__ = lambda s: mock_file
            mock_tf.return_value.__exit__ = MagicMock(return_value=False)
            mock_tf.return_value = mock_file
            app._launch_beetle()
            mock_popen.assert_called()

    def test_launch_falls_back_to_cmd_when_wt_missing(self) -> None:
        app = _make_app()
        app._state.log_lines = []
        with patch("agent.tui.app.subprocess.Popen") as mock_popen, \
             patch("agent.tui.app.tempfile.NamedTemporaryFile") as mock_tf:
            mock_file = MagicMock()
            mock_file.name = "/tmp/test.log"
            mock_tf.return_value = mock_file
            # First call (wt) raises FileNotFoundError, second call (cmd) succeeds
            mock_popen.side_effect = [FileNotFoundError, MagicMock()]
            app._launch_beetle()
            assert mock_popen.call_count == 2


class TestTuiInit:
    def test_lazy_import_returns_tui_app_class(self) -> None:
        from agent.tui import TuiApp as ImportedTuiApp
        assert ImportedTuiApp is TuiApp

    def test_unknown_attribute_raises(self) -> None:
        import agent.tui as tui_module
        with pytest.raises(AttributeError):
            _ = tui_module.NonExistent  # type: ignore[attr-defined]
