"""Unit tests for beetle/__main__.py, beetle/session.py, and beetle/tui.py."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from beetle.__main__ import main
from beetle.session import BeetleSession
from beetle.tui import BeetleTuiApp


# ---------------------------------------------------------------------------
# BeetleSession
# ---------------------------------------------------------------------------


def _make_stream_mock(deltas: list[str]):
    """Return an async context manager mock whose stream_text yields *deltas*."""
    mock_stream = MagicMock()

    async def _aenter(_):
        return mock_stream

    async def _aexit(*_):
        pass

    async def _stream_text(delta: bool = False):
        for chunk in deltas:
            yield chunk

    mock_stream.__aenter__ = _aenter
    mock_stream.__aexit__ = _aexit
    mock_stream.stream_text = _stream_text
    return mock_stream


class TestBeetleSession:
    def _make_session(self, log_lines: list[str] | None = None) -> BeetleSession:
        with patch("beetle.session.create_beetle_agent"):
            return BeetleSession(log_lines or [])

    def test_subscribe_returns_unsubscribe(self) -> None:
        session = self._make_session()
        received: list = []
        unsubscribe = session.subscribe(received.append)
        assert callable(unsubscribe)

    def test_unsubscribe_removes_listener(self) -> None:
        session = self._make_session()
        received: list = []
        unsubscribe = session.subscribe(received.append)
        unsubscribe()
        session.clear()  # would emit ClearedEvent
        assert received == []

    def test_clear_emits_cleared_event(self) -> None:
        from tui.protocol import ClearedEvent
        session = self._make_session()
        received: list = []
        session.subscribe(received.append)
        session.clear()
        assert len(received) == 1
        assert isinstance(received[0], ClearedEvent)

    def test_append_line_adds_to_buffer(self) -> None:
        session = self._make_session()
        session.append_line("hello")
        assert session._log_lines == ["hello"]

    def test_append_line_caps_at_1000(self) -> None:
        session = self._make_session()
        for i in range(1100):
            session.append_line(f"line {i}")
        assert len(session._log_lines) == 1000
        assert session._log_lines[-1] == "line 1099"

    @pytest.mark.asyncio
    async def test_prompt_emits_agent_start_and_end(self) -> None:
        from tui.protocol import AgentEndEvent, AgentStartEvent, TextDeltaEvent
        session = self._make_session(["[INF] log: hello"])
        received: list = []
        session.subscribe(received.append)

        session._agent.run_stream = MagicMock(
            return_value=_make_stream_mock(["beetle ", "response"])
        )

        await session.prompt("what happened?")

        event_types = [type(e).__name__ for e in received]
        assert "AgentStartEvent" in event_types
        assert "AgentEndEvent" in event_types
        deltas = [e for e in received if isinstance(e, TextDeltaEvent)]
        assert "".join(d.content for d in deltas) == "beetle response"
        end = next(e for e in received if isinstance(e, AgentEndEvent))
        assert end.agent_id == "beetle"

    @pytest.mark.asyncio
    async def test_prompt_emits_error_on_exception(self) -> None:
        from tui.protocol import AgentEndEvent
        session = self._make_session()
        received: list = []
        session.subscribe(received.append)

        bad_stream = MagicMock()
        bad_stream.__aenter__ = AsyncMock(side_effect=RuntimeError("boom"))
        bad_stream.__aexit__ = AsyncMock(return_value=None)
        session._agent.run_stream = MagicMock(return_value=bad_stream)

        await session.prompt("test")

        end = next(e for e in received if isinstance(e, AgentEndEvent))
        assert "[error]" in end.output


# ---------------------------------------------------------------------------
# BeetleTuiApp
# ---------------------------------------------------------------------------


class TestBeetleTuiAppInit:
    def _make_app(self, log_lines: list[str] | None = None) -> BeetleTuiApp:
        with patch("beetle.session.create_beetle_agent"):
            session = BeetleSession(log_lines or [])
        with patch("tui.app.Application"):
            return BeetleTuiApp(session, port=None)

    def test_queue_empty_on_start(self) -> None:
        app = self._make_app()
        assert app._queue.empty()

    def test_state_username_is_user_symbol(self) -> None:
        app = self._make_app()
        assert app._state.username == "((o))"

    def test_route_input_enqueues_text(self) -> None:
        app = self._make_app()
        app._route_input("why is it slow?")
        assert not app._queue.empty()
        text, *_ = app._queue.get_nowait()
        assert text == "why is it slow?"

    def test_route_input_whitespace_only_skips(self) -> None:
        app = self._make_app()
        app._route_input("   ")
        assert app._queue.empty()

    def test_route_input_adds_user_message_to_history(self) -> None:
        app = self._make_app()
        app._route_input("my question")
        assert len(app._history._messages) == 1
        assert app._history._messages[0].content == "my question"


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


class TestMain:
    def test_main_with_nonexistent_logs_file(self, tmp_path) -> None:
        """--logs pointing to a missing file is silently ignored (empty log_lines)."""
        missing = tmp_path / "missing.log"
        with patch("sys.argv", ["beetle", "--logs", str(missing)]), \
             patch("beetle.__main__.BeetleSession") as MockSession, \
             patch("beetle.__main__.BeetleTuiApp") as MockApp:
            mock_session = MagicMock()
            MockSession.return_value = mock_session
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(return_value=None)
            MockApp.return_value = mock_instance
            main()
        MockSession.assert_called_once_with([])

    def test_main_loads_logs_from_file(self, tmp_path) -> None:
        log_file = tmp_path / "test.log"
        log_file.write_text("[INF] hello\n[ERR] boom", encoding="utf-8")
        with patch("sys.argv", ["beetle", "--logs", str(log_file)]), \
             patch("beetle.__main__.BeetleSession") as MockSession, \
             patch("beetle.__main__.BeetleTuiApp") as MockApp:
            mock_session = MagicMock()
            MockSession.return_value = mock_session
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(return_value=None)
            MockApp.return_value = mock_instance
            main()
        MockSession.assert_called_once_with(["[INF] hello", "[ERR] boom"])
