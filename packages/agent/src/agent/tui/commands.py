"""Comma-command registry for the TUI.

Format: ``,<name>`` where name is a digit or a word (alphanumeric, no spaces).

Built-in commands:
    ,1      Toggle the log panel (logs ↔ main)
    ,3      List available commands
    ,q      Quit the TUI

Slash commands (handled in _route_input, not here):
    /interpret  Open beetle in a new terminal window
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .state import TuiState

_CommandFn = Callable[[list[str], TuiState, Any], None]

PREFIX = ","
_NAME_RE = re.compile(r"^[a-z0-9]+$")


@dataclass
class Command:
    name: str
    description: str
    fn: _CommandFn


@dataclass
class CommandRegistry:
    _commands: dict[str, Command] = field(default_factory=dict)

    def register(self, name: str, description: str) -> Callable[[_CommandFn], _CommandFn]:
        def decorator(fn: _CommandFn) -> _CommandFn:
            self._commands[name] = Command(name=name, description=description, fn=fn)
            return fn
        return decorator

    def is_command(self, text: str) -> bool:
        if not text.startswith(PREFIX):
            return False
        name = text[len(PREFIX):].strip().lower()
        return bool(_NAME_RE.match(name))

    def handle(self, text: str, state: TuiState, app: Any) -> bool:
        if not self.is_command(text):
            return False
        name = text[len(PREFIX):].strip().lower()
        if name in self._commands:
            self._commands[name].fn([], state, app)
        else:
            state.log_lines.append(f"[WRN] commands: unknown command ,{name}  (try ,3 for help)")
            state.active_panel = "logs"
            app.invalidate()
        return True

    @property
    def all(self) -> list[Command]:
        return sorted(self._commands.values(), key=lambda c: c.name)


registry = CommandRegistry()


@registry.register("1", "Toggle the log panel")
def _cmd_logs(args: list[str], state: TuiState, app: Any) -> None:
    state.active_panel = "main" if state.active_panel == "logs" else "logs"
    app.invalidate()


@registry.register("3", "List available commands")
def _cmd_help(args: list[str], state: TuiState, app: Any) -> None:
    state.log_lines.append("[INF] commands: ── available commands ──")
    for cmd in registry.all:
        state.log_lines.append(f"[INF] commands: ,{cmd.name:<8} {cmd.description}")
    state.log_lines.append("[INF] commands: /interpret  Open beetle in a new terminal")
    state.active_panel = "logs"
    app.invalidate()


@registry.register("q", "Quit the TUI")
def _cmd_quit(args: list[str], state: TuiState, app: Any) -> None:
    app.exit()
