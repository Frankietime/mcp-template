"""Unit tests for AgentTuiApp internals (no live MCP/API required)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from lab_mouse.deps import AgentDeps
from lab_mouse.session import AgentSession
from lab_mouse.tui.app import AgentTuiApp
from equator.protocol import AgentEndEvent, AgentStartEvent, ClearedEvent, TextDeltaEvent, ToolCallEvent, ToolResultEvent


def _make_session(deps: AgentDeps | None = None) -> AgentSession:
    deps = deps or AgentDeps(model="test-model")
    with patch("lab_mouse.session.create_agent"):
        return AgentSession(deps)


def _make_app(deps: AgentDeps | None = None) -> AgentTuiApp:
    deps = deps or AgentDeps(model="test-model")
    session = _make_session(deps)
    with patch("tui.app.Application") as MockApp:
        MockApp.return_value = MagicMock()
        app = AgentTuiApp(session, deps)
    return app


class TestAgentTuiAppInit:
    def test_state_model_name_matches_deps(self) -> None:
        app = _make_app()
        assert app._state.model_name == "test-model"

    def test_state_starts_not_thinking(self) -> None:
        app = _make_app()
        assert app._state.thinking is False

    def test_state_starts_mcp_disconnected(self) -> None:
        app = _make_app()
        assert app._state.mcp_connected is False

    def test_msg_queue_is_empty(self) -> None:
        app = _make_app()
        assert app._msg_queue.empty()


class TestHandleEvent:
    def test_text_delta_appends_to_stream(self) -> None:
        app = _make_app()
        app._state.thinking = True
        app._handle_event(TextDeltaEvent(content="hel"))
        app._handle_event(TextDeltaEvent(content="lo"))
        assert app._history._streaming is not None
        assert app._history._streaming.content == "hello"

    def test_agent_start_sets_thinking(self) -> None:
        app = _make_app()
        app._handle_event(AgentStartEvent())
        assert app._state.thinking is True

    def test_agent_end_clears_thinking(self) -> None:
        app = _make_app()
        app._state.thinking = True
        app._handle_event(AgentEndEvent(output="done"))
        assert app._state.thinking is False

    def test_agent_end_finalises_message(self) -> None:
        app = _make_app()
        app._handle_event(AgentStartEvent())
        app._handle_event(TextDeltaEvent(content="hi"))
        app._handle_event(AgentEndEvent(output="hi"))
        assert len(app._history._messages) == 1
        assert app._history._messages[0].content == "hi"

    def test_cleared_calls_history_clear(self) -> None:
        app = _make_app()
        app._history.add_user_message("test")
        app._handle_event(ClearedEvent())
        assert app._history._messages == []
        assert app._state.thinking is False

    def test_tool_call_adds_tool_row(self) -> None:
        app = _make_app()
        app._handle_event(ToolCallEvent(name="search"))
        assert len(app._history._messages) == 1
        assert "search" in app._history._messages[0].content

    def test_tool_result_completes_tool_row(self) -> None:
        app = _make_app()
        app._handle_event(ToolCallEvent(name="search"))
        app._handle_event(ToolResultEvent())
        assert app._history._messages[0].complete is True

    def test_handle_event_calls_invalidate(self) -> None:
        app = _make_app()
        app._handle_event(ClearedEvent())
        app._app.invalidate.assert_called()


class TestAgentTuiAppHandlers:
    def test_handle_clear_calls_session_clear(self) -> None:
        app = _make_app()
        app._session.clear = MagicMock()
        app._handle_clear()
        app._session.clear.assert_called_once()

    def test_handle_quit_calls_exit(self) -> None:
        app = _make_app()
        app._handle_quit()
        app._app.exit.assert_called_once()


class TestRouteInput:
    def test_action_command_mutates_state(self) -> None:
        app = _make_app()
        app._route_input("/help")
        assert app._state.active_panel == "logs"
        assert app._msg_queue.empty()

    def test_message_goes_to_msg_queue(self) -> None:
        app = _make_app()
        app._route_input("hello agent")
        assert not app._msg_queue.empty()

    def test_interpret_dispatched_via_registry(self) -> None:
        """interpret is now an ACTION in the lab_mouse registry."""
        app = _make_app()
        with patch.object(app, "_launch_beetle") as mock_launch:
            app._route_input("/interpret")
            mock_launch.assert_called_once()

    def test_interpret_does_not_enqueue_message(self) -> None:
        app = _make_app()
        with patch.object(app, "_launch_beetle"):
            app._route_input("/interpret")
        assert app._msg_queue.empty()


class TestRouteInputCommandKinds:
    def test_action_command_mutates_state(self) -> None:
        app = _make_app()
        app._route_input("/help")  # /help is ACTION — opens logs panel
        assert app._state.active_panel == "logs"
        assert app._msg_queue.empty()

    def test_prompt_command_pre_fills_buffer(self) -> None:
        from equator.commands import CommandKind
        app = _make_app()
        app._cmd_registry.register(
            "tpltest", "fill template",
            kind=CommandKind.PROMPT,
            template="Do: ",
        )(lambda *_: None)
        app._route_input("/tpltest")
        assert app._input_ctrl.buffer.text == "Do: "
        assert app._msg_queue.empty()

    def test_prompt_command_does_not_enqueue(self) -> None:
        from equator.commands import CommandKind
        app = _make_app()
        app._cmd_registry.register(
            "tpltest2", "fill 2",
            kind=CommandKind.PROMPT,
            template="stub",
        )(lambda *_: None)
        app._route_input("/tpltest2")
        assert app._msg_queue.empty()

    def test_script_command_sends_template_to_agent(self) -> None:
        from equator.commands import CommandKind
        app = _make_app()
        app._cmd_registry.register(
            "runtest1", "run script",
            kind=CommandKind.SCRIPT,
            template="Summarise context",
        )(lambda *_: None)
        app._route_input("/runtest1")
        assert not app._msg_queue.empty()
        assert app._msg_queue.get_nowait() == "Summarise context"

    def test_script_command_adds_to_history(self) -> None:
        from equator.commands import CommandKind
        app = _make_app()
        app._cmd_registry.register(
            "runtest2", "run 2",
            kind=CommandKind.SCRIPT,
            template="Execute plan",
        )(lambda *_: None)
        before = len(app._history._messages)
        app._route_input("/runtest2")
        assert len(app._history._messages) == before + 1
        assert app._history._messages[-1].content == "Execute plan"


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
    def test_launch_writes_logs_and_spawns_process(self) -> None:
        app = _make_app()
        app._state.log_lines = ["[INF] agent: hello", "[ERR] agent: boom"]
        with patch("lab_mouse.tui.app.subprocess.Popen") as mock_popen, \
             patch("lab_mouse.tui.app.tempfile.NamedTemporaryFile") as mock_tf:
            mock_file = MagicMock()
            mock_file.name = "/tmp/test.log"
            mock_tf.return_value = mock_file
            app._launch_beetle()
            mock_popen.assert_called()

    def test_launch_falls_back_to_cmd_when_wt_missing(self) -> None:
        app = _make_app()
        app._state.log_lines = []
        with patch("lab_mouse.tui.app.subprocess.Popen") as mock_popen, \
             patch("lab_mouse.tui.app.tempfile.NamedTemporaryFile") as mock_tf:
            mock_file = MagicMock()
            mock_file.name = "/tmp/test.log"
            mock_tf.return_value = mock_file
            mock_popen.side_effect = [FileNotFoundError, MagicMock()]
            app._launch_beetle()
            assert mock_popen.call_count == 2


class TestTuiAlias:
    def test_tui_app_alias_is_agent_tui_app(self) -> None:
        from lab_mouse.tui.app import TuiApp
        assert TuiApp is AgentTuiApp

    def test_lazy_import_from_tui_module(self) -> None:
        from lab_mouse.tui import TuiApp
        assert TuiApp is AgentTuiApp

    def test_unknown_attribute_raises(self) -> None:
        import lab_mouse.tui as tui_module
        with pytest.raises(AttributeError):
            _ = tui_module.NonExistent  # type: ignore[attr-defined]
