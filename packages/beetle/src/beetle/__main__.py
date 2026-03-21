"""Entry point for ``uv run beetle`` / ``python -m beetle``."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .agent import BEETLE_SYMBOL
from .app import BeetleApp


def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"{BEETLE_SYMBOL} beetle — logs interpreter chatbot"
    )
    parser.add_argument("--logs", type=Path, default=None, help="Path to log file")
    args = parser.parse_args()

    log_lines: list[str] = []
    if args.logs and args.logs.exists():
        log_lines = args.logs.read_text(encoding="utf-8").splitlines()

    asyncio.run(BeetleApp(log_lines).run())


if __name__ == "__main__":
    main()
