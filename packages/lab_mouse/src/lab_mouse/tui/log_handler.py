"""Custom logging handler that routes records into TuiState."""

from __future__ import annotations

import logging
import logging.handlers
import os
import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")

from tui.state import TuiState

_MAX_LINES = 500  # rolling window to avoid unbounded memory growth

_LEVEL_PREFIX = {
    logging.DEBUG: "DBG",
    logging.INFO: "INF",
    logging.WARNING: "WRN",
    logging.ERROR: "ERR",
    logging.CRITICAL: "CRT",
}


class TuiLogHandler(logging.Handler):
    """Appends formatted log lines to ``state.log_lines``."""

    def __init__(self, state: TuiState, app, refresh_logs: Callable[[], None]) -> None:
        super().__init__()
        self._state = state
        self._app = app
        self._refresh_logs = refresh_logs

    def emit(self, record: logging.LogRecord) -> None:
        try:
            prefix = _LEVEL_PREFIX.get(record.levelno, "???")
            name = record.name.removeprefix("pydantic_ai.").removeprefix("pydantic_ai")
            name = name.lstrip(".") or "pydantic_ai"
            line = _ANSI_ESCAPE.sub("", f"[{prefix}] {name}: {record.getMessage()}")
            if record.exc_info:
                line += f"\n  {self.formatException(record.exc_info)}"

            lines = self._state.log_lines
            lines.append(line)
            if len(lines) > _MAX_LINES:
                del lines[: len(lines) - _MAX_LINES]

            self._refresh_logs()
            if self._state.active_panel == "logs":
                self._app.invalidate()
        except Exception:  # noqa: BLE001
            self.handleError(record)


def _make_file_handler() -> logging.FileHandler:
    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    fh = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    return fh


_NAMED_LOGGERS = ("pydantic_ai", "httpx", "mcp", "lab_mouse")


def attach_log_handler(
    state: TuiState,
    app,
    refresh_logs: Callable[[], None],
) -> tuple[TuiLogHandler, logging.FileHandler, logging.Handler | None]:
    """Register ``TuiLogHandler`` on key loggers and a FileHandler on the root logger.

    Returns ``(tui_handler, file_handler, beetle_handler)`` where ``beetle_handler``
    is ``None`` when ``BEETLE_PORT`` is not set.
    """
    handler = TuiLogHandler(state, app, refresh_logs)
    handler.setLevel(logging.DEBUG)

    file_handler = _make_file_handler()

    for name in _NAMED_LOGGERS:
        logger = logging.getLogger(name)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    # File handler on root — captures everything from every library
    root = logging.getLogger()
    root.addHandler(file_handler)
    root.setLevel(logging.DEBUG)

    beetle_handler: logging.Handler | None = None
    beetle_port = os.getenv("BEETLE_PORT")
    if beetle_port:
        from beetle.log_server import BeetleHandler  # optional dep — only when beetle is running
        beetle_handler = BeetleHandler(port=int(beetle_port))
        beetle_handler.setLevel(logging.DEBUG)
        for name in _NAMED_LOGGERS:
            logging.getLogger(name).addHandler(beetle_handler)

    return handler, file_handler, beetle_handler


def detach_log_handler(
    handler: TuiLogHandler,
    file_handler: logging.FileHandler,
    beetle_handler: logging.Handler | None = None,
) -> None:
    for name in ("pydantic_ai", "httpx", "mcp", "lab_mouse"):
        lg = logging.getLogger(name)
        lg.removeHandler(handler)
        if beetle_handler:
            lg.removeHandler(beetle_handler)
    root = logging.getLogger()
    root.removeHandler(file_handler)
    file_handler.close()
    if beetle_handler:
        beetle_handler.close()
