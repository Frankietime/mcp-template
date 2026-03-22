"""Entry point for ``uv run beetle`` / ``python -m beetle``."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    for parent in [Path.cwd(), *Path.cwd().parents]:
        env_file = parent / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            return


_load_env()

from .agent import BEETLE_SYMBOL
from .log_server import DEFAULT_PORT
from .session import BeetleSession
from .tui import BeetleTuiApp


def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"{BEETLE_SYMBOL} beetle — logs interpreter chatbot"
    )
    parser.add_argument("--logs", type=Path, default=None, help="Path to log file")
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT,
        help=f"TCP port for log socket server (default {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--no-server", action="store_true",
        help="Disable the log socket server (useful with --logs for static queries)",
    )
    args = parser.parse_args()

    stdin_mode = not sys.stdin.isatty()
    port = None if args.no_server else args.port

    log_lines: list[str] = []
    if args.logs and args.logs.exists():
        log_lines = args.logs.read_text(encoding="utf-8").splitlines()

    session = BeetleSession(log_lines)
    asyncio.run(BeetleTuiApp(session, stdin_mode=stdin_mode, port=port).run())


if __name__ == "__main__":
    main()
