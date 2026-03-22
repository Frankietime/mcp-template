"""Unit tests for tui/log_handler.py and tui/components/logs.py."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

from lab_mouse.tui.log_handler import (
    TuiLogHandler,
    attach_log_handler,
    detach_log_handler,
)
from equator.components.logs import LogsControl, _color_line
from equator.state import TuiState


# ---------------------------------------------------------------------------
# logs._color_line helper (replaces removed _LogLexer)
# ---------------------------------------------------------------------------

class TestColorLine:
    def test_inf_tag_gets_log_inf_style(self) -> None:
        tokens = _color_line("[INF] foo: bar")
        styles = [s for s, _ in tokens]
        assert "class:log.inf" in styles

    def test_err_tag_gets_log_err_style(self) -> None:
        tokens = _color_line("[ERR] foo: oops")
        styles = [s for s, _ in tokens]
        assert "class:log.err" in styles

    def test_wrn_tag_gets_log_wrn_style(self) -> None:
        tokens = _color_line("[WRN] foo: careful")
        styles = [s for s, _ in tokens]
        assert "class:log.wrn" in styles

    def test_dbg_tag_gets_log_dbg_style(self) -> None:
        tokens = _color_line("[DBG] foo: verbose")
        styles = [s for s, _ in tokens]
        assert "class:log.dbg" in styles

    def test_crt_tag_gets_log_crt_style(self) -> None:
        tokens = _color_line("[CRT] foo: critical")
        styles = [s for s, _ in tokens]
        assert "class:log.crt" in styles

    def test_plain_line_has_no_level_style(self) -> None:
        tokens = _color_line("no bracket prefix here")
        styles = [s for s, _ in tokens]
        assert not any(s.startswith("class:log.") for s in styles)

    def test_unknown_tag_has_no_level_style(self) -> None:
        tokens = _color_line("[XYZ] foo: unknown")
        styles = [s for s, _ in tokens]
        assert not any("log.inf" in s or "log.err" in s for s in styles)


# ---------------------------------------------------------------------------
# LogsControl — now takes (list[str], name) not (TuiState)
# ---------------------------------------------------------------------------

class TestLogsControl:
    def test_container_is_created(self) -> None:
        lines: list[str] = []
        ctrl = LogsControl(lines, "logs")
        assert ctrl.container is not None

    def test_page_back_and_forward_do_not_raise(self) -> None:
        lines = [f"[INF] a: line {i}" for i in range(50)]
        ctrl = LogsControl(lines, "logs")
        ctrl.page_back()
        ctrl.page_forward()


# ---------------------------------------------------------------------------
# TuiLogHandler.emit
# ---------------------------------------------------------------------------

def _make_handler(state=None):
    if state is None:
        state = TuiState()
    app = MagicMock()
    refresh = MagicMock()
    handler = TuiLogHandler(state, app, refresh)
    return handler, state, app, refresh


def _record(name: str, level: int, msg: str) -> logging.LogRecord:
    return logging.LogRecord(
        name=name, level=level, pathname="", lineno=0,
        msg=msg, args=(), exc_info=None,
    )


class TestTuiLogHandlerEmit:
    def test_info_record_appended(self) -> None:
        handler, state, app, refresh = _make_handler()
        handler.emit(_record("httpx", logging.INFO, "GET /api"))
        assert any("GET /api" in line for line in state.log_lines)

    def test_debug_record_appended(self) -> None:
        handler, state, app, refresh = _make_handler()
        handler.emit(_record("httpx", logging.DEBUG, "debug detail"))
        assert any("debug detail" in line for line in state.log_lines)

    def test_pydantic_ai_prefix_stripped(self) -> None:
        handler, state, app, refresh = _make_handler()
        handler.emit(_record("pydantic_ai.agent", logging.INFO, "running"))
        assert any("agent" in line for line in state.log_lines)
        assert not any("pydantic_ai.agent" in line for line in state.log_lines)

    def test_refresh_called_on_emit(self) -> None:
        handler, state, app, refresh = _make_handler()
        handler.emit(_record("httpx", logging.INFO, "ping"))
        refresh.assert_called()

    def test_invalidate_called_when_logs_visible(self) -> None:
        state = TuiState(active_panel="logs")
        handler, state, app, refresh = _make_handler(state=state)
        handler.emit(_record("httpx", logging.INFO, "ping"))
        app.invalidate.assert_called()

    def test_invalidate_not_called_when_logs_hidden(self) -> None:
        state = TuiState()  # active_panel="main"
        handler, state, app, refresh = _make_handler(state=state)
        handler.emit(_record("httpx", logging.INFO, "ping"))
        app.invalidate.assert_not_called()

    def test_rolling_window_caps_at_500(self) -> None:
        handler, state, app, refresh = _make_handler()
        for i in range(510):
            handler.emit(_record("httpx", logging.INFO, f"line {i}"))
        assert len(state.log_lines) == 500

    def test_level_prefix_in_output(self) -> None:
        handler, state, app, refresh = _make_handler()
        handler.emit(_record("httpx", logging.WARNING, "something odd"))
        assert any("[WRN]" in line for line in state.log_lines)


# ---------------------------------------------------------------------------
# attach_log_handler / detach_log_handler
# ---------------------------------------------------------------------------

class TestAttachDetach:
    def test_attach_adds_handler_to_pydantic_ai(self) -> None:
        state = TuiState()
        app = MagicMock()
        handler, fh, _ = attach_log_handler(state, app, refresh_logs=MagicMock())
        logger = logging.getLogger("pydantic_ai")
        assert handler in logger.handlers
        detach_log_handler(handler, fh)

    def test_attach_adds_handler_to_httpx(self) -> None:
        state = TuiState()
        app = MagicMock()
        handler, fh, _ = attach_log_handler(state, app, refresh_logs=MagicMock())
        logger = logging.getLogger("httpx")
        assert handler in logger.handlers
        detach_log_handler(handler, fh)

    def test_detach_removes_handler(self) -> None:
        state = TuiState()
        app = MagicMock()
        handler, fh, _ = attach_log_handler(state, app, refresh_logs=MagicMock())
        detach_log_handler(handler, fh)
        for name in ("pydantic_ai", "httpx", "mcp"):
            assert handler not in logging.getLogger(name).handlers
