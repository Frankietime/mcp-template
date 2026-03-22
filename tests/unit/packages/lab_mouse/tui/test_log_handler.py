"""Unit tests for tui/log_handler.py and tui/components/logs.py."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

from lab_mouse.tui.log_handler import (
    TuiLogHandler,
    attach_log_handler,
    detach_log_handler,
)
from tui.components.logs import LogsControl, _LogLexer
from tui.state import TuiState


# ---------------------------------------------------------------------------
# logs._LogLexer helper
# ---------------------------------------------------------------------------

def _lex_line(line: str):
    """Return the style-tuples list for a single log line via _LogLexer."""
    from prompt_toolkit.document import Document
    doc = Document(line)
    return _LogLexer().lex_document(doc)(0)


class TestLogLexer:
    def test_inf_tag_gets_log_inf_style(self) -> None:
        tokens = _lex_line("[INF] foo: bar")
        styles = [s for s, _ in tokens]
        assert "class:log.inf" in styles

    def test_err_tag_gets_log_err_style(self) -> None:
        tokens = _lex_line("[ERR] foo: oops")
        styles = [s for s, _ in tokens]
        assert "class:log.err" in styles

    def test_wrn_tag_gets_log_wrn_style(self) -> None:
        tokens = _lex_line("[WRN] foo: careful")
        styles = [s for s, _ in tokens]
        assert "class:log.wrn" in styles

    def test_dbg_tag_gets_log_dbg_style(self) -> None:
        tokens = _lex_line("[DBG] foo: verbose")
        styles = [s for s, _ in tokens]
        assert "class:log.dbg" in styles

    def test_crt_tag_gets_log_crt_style(self) -> None:
        tokens = _lex_line("[CRT] foo: critical")
        styles = [s for s, _ in tokens]
        assert "class:log.crt" in styles

    def test_plain_line_has_no_style(self) -> None:
        tokens = _lex_line("no bracket prefix here")
        assert tokens == [("", "no bracket prefix here")]

    def test_unknown_tag_has_no_style(self) -> None:
        tokens = _lex_line("[XYZ] foo: unknown")
        assert tokens == [("", "[XYZ] foo: unknown")]


# ---------------------------------------------------------------------------
# LogsControl
# ---------------------------------------------------------------------------

class TestLogsControl:
    def test_initial_buffer_is_empty(self) -> None:
        ctrl = LogsControl(TuiState())
        assert ctrl.buffer.text == ""

    def test_refresh_syncs_log_lines(self) -> None:
        state = TuiState(log_lines=["[INF] a: one", "[ERR] b: two"])
        ctrl = LogsControl(state)
        ctrl.refresh()
        assert "one" in ctrl.buffer.text
        assert "two" in ctrl.buffer.text

    def test_refresh_cursor_at_end(self) -> None:
        state = TuiState(log_lines=["[INF] a: hello"])
        ctrl = LogsControl(state)
        ctrl.refresh()
        assert ctrl.buffer.cursor_position == len(ctrl.buffer.text)

    def test_refresh_empty_logs_clears_buffer(self) -> None:
        state = TuiState(log_lines=["[INF] a: old"])
        ctrl = LogsControl(state)
        ctrl.refresh()
        state.log_lines.clear()
        ctrl.refresh()
        assert ctrl.buffer.text == ""

    def test_buffer_control_is_focusable(self) -> None:
        ctrl = LogsControl(TuiState())
        assert ctrl.buffer_control.focusable()


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
        handler, fh = attach_log_handler(state, app, refresh_logs=MagicMock())
        logger = logging.getLogger("pydantic_ai")
        assert handler in logger.handlers
        detach_log_handler(handler, fh)

    def test_attach_adds_handler_to_httpx(self) -> None:
        state = TuiState()
        app = MagicMock()
        handler, fh = attach_log_handler(state, app, refresh_logs=MagicMock())
        logger = logging.getLogger("httpx")
        assert handler in logger.handlers
        detach_log_handler(handler, fh)

    def test_detach_removes_handler(self) -> None:
        state = TuiState()
        app = MagicMock()
        handler, fh = attach_log_handler(state, app, refresh_logs=MagicMock())
        detach_log_handler(handler, fh)
        for name in ("pydantic_ai", "httpx", "mcp"):
            assert handler not in logging.getLogger(name).handlers
