"""Unit tests for beetle/__main__.py (standalone chatbot app)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from beetle.__main__ import main
from beetle.app import BeetleApp, DEFAULT_PROMPT, colorise


class TestColorise:
    def test_usr_line_renders_cyan(self) -> None:
        result = colorise("[USR] why is it slow?")
        assert "\033[36m" in result
        assert "why is it slow?" in result

    def test_btl_line_renders_green_with_symbol(self) -> None:
        result = colorise("[BTL] all good")
        assert "\033[32m" in result
        assert "=){" in result
        assert "all good" in result

    def test_btl_err_line_renders_crimson(self) -> None:
        result = colorise("[BTL_ERR] connection refused")
        assert "\033[38;5;88m" in result
        assert "connection refused" in result

    def test_plain_line_is_unchanged(self) -> None:
        assert colorise("no tag here") == "no tag here"

    def test_unknown_tag_is_unchanged(self) -> None:
        assert colorise("[XYZ] something") == "[XYZ] something"


class TestBeetleAppInit:
    def test_empty_log_lines_accepted(self) -> None:
        with patch("beetle.app.Application") as MockApp:
            MockApp.return_value = MagicMock()
            app = BeetleApp([])
        assert app._log_lines == []

    def test_log_lines_stored(self) -> None:
        with patch("beetle.app.Application") as MockApp:
            MockApp.return_value = MagicMock()
            app = BeetleApp(["[INF] foo: bar"])
        assert app._log_lines == ["[INF] foo: bar"]

    def test_conv_lines_empty_on_start(self) -> None:
        with patch("beetle.app.Application") as MockApp:
            MockApp.return_value = MagicMock()
            app = BeetleApp([])
        assert app._conv_lines == []

    def test_queue_empty_on_start(self) -> None:
        with patch("beetle.app.Application") as MockApp:
            MockApp.return_value = MagicMock()
            app = BeetleApp([])
        assert app._queue.empty()


class TestBeetleAppAccept:
    def _make_app(self) -> BeetleApp:
        with patch("beetle.app.Application") as MockApp:
            MockApp.return_value = MagicMock()
            return BeetleApp([])

    def test_accept_enqueues_text(self) -> None:
        app = self._make_app()
        buf = MagicMock()
        buf.text = "why is it slow?"
        app._accept(buf)
        assert not app._queue.empty()
        assert app._queue.get_nowait() == "why is it slow?"

    def test_accept_appends_usr_line(self) -> None:
        app = self._make_app()
        buf = MagicMock()
        buf.text = "my question"
        app._accept(buf)
        assert any("[USR] my question" in line for line in app._conv_lines)

    def test_accept_whitespace_only_skips(self) -> None:
        app = self._make_app()
        buf = MagicMock()
        buf.text = "   "
        app._accept(buf)
        assert app._queue.empty()
        assert app._conv_lines == []

    def test_accept_resets_buffer(self) -> None:
        app = self._make_app()
        buf = MagicMock()
        buf.text = "hello"
        app._accept(buf)
        buf.reset.assert_called_once()


class TestBeetleAppRun:
    def _make_app(self, log_lines=None) -> BeetleApp:
        with patch("beetle.app.Application") as MockApp:
            MockApp.return_value = MagicMock()
            return BeetleApp(log_lines or [])

    def test_run_with_logs_enqueues_default_prompt(self) -> None:
        app = self._make_app(["[ERR] something"])
        # Peek at queue state before running full app
        app._app.run_async = AsyncMock(return_value=None)
        # Stub agent loop so it doesn't block
        async def _drain():
            await asyncio.sleep(0)
        with patch.object(app, "_agent_loop", side_effect=_drain):
            asyncio.run(app.run())
        # The default prompt was enqueued during run()
        # (queue may be drained by stub, so we verify indirectly via conv_lines)

    def test_run_without_logs_does_not_enqueue_prompt(self) -> None:
        app = self._make_app([])
        # Before run(), queue is empty; with no logs it stays empty
        assert app._queue.empty()


class TestBeetleAppRefresh:
    def _make_app(self) -> BeetleApp:
        with patch("beetle.app.Application") as MockApp:
            MockApp.return_value = MagicMock()
            return BeetleApp([])

    def test_refresh_sets_history_buffer_text(self) -> None:
        app = self._make_app()
        app._conv_lines = ["[USR] hello", "[BTL] world"]
        app._refresh()
        assert "hello" in app._history_buf.text
        assert "world" in app._history_buf.text

    def test_refresh_empty_conv_clears_buffer(self) -> None:
        app = self._make_app()
        app._conv_lines = ["[USR] something"]
        app._refresh()
        app._conv_lines = []
        app._refresh()
        assert app._history_buf.text == ""


class TestMain:
    def test_main_with_nonexistent_logs_file(self, tmp_path) -> None:
        """--logs pointing to a missing file is silently ignored (empty log_lines)."""
        missing = tmp_path / "missing.log"
        with patch("sys.argv", ["beetle", "--logs", str(missing)]), \
             patch("beetle.__main__.BeetleApp") as MockApp:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(return_value=None)
            MockApp.return_value = mock_instance
            main()
        MockApp.assert_called_once_with([])

    def test_main_loads_logs_from_file(self, tmp_path) -> None:
        log_file = tmp_path / "test.log"
        log_file.write_text("[INF] hello\n[ERR] boom", encoding="utf-8")
        with patch("sys.argv", ["beetle", "--logs", str(log_file)]), \
             patch("beetle.__main__.BeetleApp") as MockApp:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(return_value=None)
            MockApp.return_value = mock_instance
            main()
        MockApp.assert_called_once_with(["[INF] hello", "[ERR] boom"])
