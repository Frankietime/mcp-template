"""BeetleLogServer — receives log records over TCP as newline-delimited JSON.

Protocol (sender side):
    Each log record is one JSON object followed by a newline:
        {"level": 20, "name": "myapp", "msg": "hello", "exc": null}\n

    ``level`` is a stdlib logging level integer (10=DEBUG, 20=INFO, …).

Any Python app can connect with the bundled BeetleHandler or by copy-pasting the
8-line snippet in BeetleHandler's docstring.

The server binds exclusively to 127.0.0.1 — local development only.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import Callable

from .session import BeetleSession

DEFAULT_PORT = 9020

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")

_LEVEL_PREFIX = {
    logging.DEBUG: "DBG",
    logging.INFO: "INF",
    logging.WARNING: "WRN",
    logging.ERROR: "ERR",
    logging.CRITICAL: "CRT",
}


def _format_line(level: int, name: str, msg: str, exc: str | None) -> str:
    """Format a log record the same way TuiLogHandler does in packages/agent."""
    prefix = _LEVEL_PREFIX.get(level, "???")
    name = name.removeprefix("pydantic_ai.").removeprefix("pydantic_ai")
    name = name.lstrip(".") or "pydantic_ai"
    line = _ANSI_ESCAPE.sub("", f"[{prefix}] {name}: {msg}")
    if exc:
        line += f"\n  {exc}"
    return line


async def _handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    session: BeetleSession,
    invalidate: Callable[[], None],
) -> None:
    """Read newline-delimited JSON records and feed them to the session buffer."""
    try:
        async for raw in reader:
            line = raw.decode(errors="replace").strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                formatted = _format_line(
                    rec.get("level", logging.INFO),
                    rec.get("name", ""),
                    rec.get("msg", ""),
                    rec.get("exc"),
                )
            except (json.JSONDecodeError, KeyError):
                formatted = line  # pass raw line through if it isn't JSON
            session.append_line(formatted)
            invalidate()
    except (asyncio.IncompleteReadError, ConnectionResetError):
        pass
    finally:
        writer.close()


async def log_server_loop(
    session: BeetleSession,
    invalidate: Callable[[], None],
    port: int = DEFAULT_PORT,
) -> None:
    """Start TCP server on localhost; accept clients until cancelled."""
    try:
        server = await asyncio.start_server(
            lambda r, w: _handle_client(r, w, session, invalidate),
            host="127.0.0.1",
            port=port,
        )
    except OSError as e:
        session.append_line(f"[WRN] log_server: port {port} already in use — log server disabled ({e.strerror})")
        invalidate()
        return
    async with server:
        await server.serve_forever()


# ---------------------------------------------------------------------------
# BeetleHandler — convenience logging.Handler for Python apps


class BeetleHandler(logging.Handler):
    """Sends log records to a running beetle instance over TCP.

    Usage (any Python app):

        from beetle.log_server import BeetleHandler
        logging.getLogger().addHandler(BeetleHandler())

    Copy-paste alternative (no beetle dependency required):

        import json, socket, logging, traceback

        class BeetleHandler(logging.Handler):
            def __init__(self, host="localhost", port=9020):
                super().__init__()
                self._sock = socket.create_connection((host, port))
            def emit(self, record):
                exc = traceback.format_exc() if record.exc_info else None
                data = json.dumps({"level": record.levelno, "name": record.name,
                                   "msg": record.getMessage(), "exc": exc}) + "\\n"
                try:
                    self._sock.sendall(data.encode())
                except OSError:
                    self.handleError(record)
    """

    def __init__(self, host: str = "localhost", port: int = DEFAULT_PORT) -> None:
        super().__init__()
        import socket as _socket
        self._sock = _socket.create_connection((host, port))

    def emit(self, record: logging.LogRecord) -> None:
        import traceback
        exc = traceback.format_exc() if record.exc_info else None
        payload = json.dumps({
            "level": record.levelno,
            "name": record.name,
            "msg": record.getMessage(),
            "exc": exc,
        }) + "\n"
        try:
            self._sock.sendall(payload.encode())
        except OSError:
            self.handleError(record)
