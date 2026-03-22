"""Slash-command registry for the TUI.

Format: ``/<name> [args...]``

Built-in commands:
    /help           Show welcome and key bindings
    /logs [levels]  Set active log levels (e.g. /logs err crt  /logs all  /logs none)
    /q              Quit the TUI

Command kinds:
    ACTION  Execute TUI-side logic (default).
    PROMPT  Pre-fill the input box with a template; user edits then sends.
    SCRIPT  Immediately send the template to the agent without editing.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document

from .state import TuiState

_CommandFn = Callable[[list[str], TuiState, Any], None]

PREFIX = "/"
_NAME_RE = re.compile(r"^[a-z0-9]+$")


class CommandKind(Enum):
    ACTION = auto()  # execute TUI-side logic (existing behaviour)
    PROMPT = auto()  # pre-fill the input box; user edits then sends
    SCRIPT = auto()  # immediately send template to the agent


@dataclass
class Command:
    name: str
    description: str
    fn: _CommandFn
    kind: CommandKind = CommandKind.ACTION
    template: str | None = None


@dataclass
class CommandRegistry:
    _commands: dict[str, Command] = field(default_factory=dict)

    def register(
        self,
        name: str,
        description: str,
        *,
        kind: CommandKind = CommandKind.ACTION,
        template: str | None = None,
    ) -> Callable[[_CommandFn], _CommandFn]:
        def decorator(fn: _CommandFn) -> _CommandFn:
            self._commands[name] = Command(
                name=name, description=description, fn=fn, kind=kind, template=template
            )
            return fn
        return decorator

    def is_command(self, text: str) -> bool:
        if not text.startswith(PREFIX):
            return False
        parts = text[len(PREFIX):].strip().lower().split()
        return bool(parts and _NAME_RE.match(parts[0]))

    def get(self, name: str) -> Command | None:
        return self._commands.get(name)

    def handle(self, text: str, state: TuiState, app: Any) -> bool:
        if not self.is_command(text):
            return False
        parts = text[len(PREFIX):].strip().lower().split()
        name, args = parts[0], parts[1:]
        if name in self._commands:
            self._commands[name].fn(args, state, app)
        else:
            state.internal_log_lines.append(f"[WRN] commands: unknown command /{name}  (try /help)")
            state.active_panel = "internal_logs"
            app.invalidate()
        return True

    def extend(self) -> CommandRegistry:
        """Return a new registry pre-populated with a snapshot of these commands.

        Use this to create app-specific registries that inherit common commands
        without polluting the shared registry with app-specific entries.
        """
        child = CommandRegistry()
        child._commands = dict(self._commands)
        return child

    @property
    def all(self) -> list[Command]:
        return sorted(self._commands.values(), key=lambda c: c.name)


class SlashCompleter(Completer):
    """Yields slash-command completions from a CommandRegistry.

    Only activates when the buffer text starts with '/'.
    Display shows the full ``/name`` and meta shows the description.
    """

    def __init__(self, registry: CommandRegistry) -> None:
        self._registry = registry

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        text = document.text_before_cursor
        if not text.startswith(PREFIX):
            return
        partial = text[len(PREFIX):]
        if " " in partial:
            return
        for cmd in self._registry.all:
            if cmd.name.startswith(partial):
                yield Completion(
                    text=cmd.name,
                    start_position=-len(partial),
                    display=f"/{cmd.name}",
                    display_meta=cmd.description,
                )


registry = CommandRegistry()


_ALL_LEVELS = ("DBG", "INF", "WRN", "ERR", "CRT")


@registry.register("help", "Show key bindings and available commands")
def _cmd_help(args: list[str], state: TuiState, app: Any) -> None:
    # Use the app's own registry so app-specific commands appear in help.
    # Falls back to the base registry when app is a mock or has no registry.
    _maybe = getattr(app, "cmd_registry", None)
    cmd_reg: CommandRegistry = _maybe if isinstance(_maybe, CommandRegistry) else registry
    lines = [
        "[INF] help: ══════════════════════════════════════════",
        f"[INF] help:   {state.agent_name}",
        "[INF] help: ══════════════════════════════════════════",
        "[INF] help:   Commands",
        "[INF] help: ──────────────────────────────────────────",
    ]
    for cmd in cmd_reg.all:
        lines.append(f"[INF] help:   /{cmd.name:<12} {cmd.description}")
    lines += [
        "[INF] help: ──────────────────────────────────────────",
        "[INF] help:   Key bindings",
        "[INF] help: ──────────────────────────────────────────",
        "[INF] help:   Enter          Send message",
        "[INF] help:   Esc+Enter      Insert newline",
        "[INF] help:   Ctrl+O         Toggle logs panel",
        "[INF] help:   Tab            Toggle help sidebar",
        "[INF] help:   F2             Toggle inspect expansion",
        "[INF] help:   Shift+Tab      Toggle internal logs",
        "[INF] help:   ↑ / ↓          Navigate messages (when input empty)",
        "[INF] help:   ← / →          Cycle tool calls / page logs",
        "[INF] help:   Esc            Clear message cursor",
        "[INF] help:   Ctrl+X         Quit",
        "[INF] help: ══════════════════════════════════════════",
    ]
    state.internal_log_lines.extend(lines)
    state.active_panel = "internal_logs"
    app.invalidate()


@registry.register("logs", "Set active log levels  e.g. /logs err crt · /logs all · /logs none")
def _cmd_logs(args: list[str], state: TuiState, app: Any) -> None:
    if not args:
        active = " ".join(lvl for lvl in _ALL_LEVELS if lvl in state.active_levels) or "none"
        state.internal_log_lines.append(f"[INF] logs: active levels → {active}  (use /logs all·none·dbg·inf·wrn·err·crt)")
        state.active_panel = "internal_logs"
        app.invalidate()
        return
    joined = " ".join(args)
    if joined in ("all", "*"):
        state.active_levels = set(_ALL_LEVELS)
    elif joined in ("none", "off", "0"):
        state.active_levels = set()
    else:
        requested = {a.upper() for a in args}
        valid = requested & set(_ALL_LEVELS)
        unknown = requested - set(_ALL_LEVELS)
        if unknown:
            state.internal_log_lines.append(f"[WRN] logs: unknown level(s): {', '.join(sorted(unknown))}")
        state.active_levels = valid
    active = " ".join(lvl for lvl in _ALL_LEVELS if lvl in state.active_levels) or "none"
    state.internal_log_lines.append(f"[INF] logs: active levels → {active}")
    state.active_panel = "internal_logs"
    app.invalidate()


@registry.register("model", "Open model selector (fetches from Ollama)")
def _cmd_model(args: list[str], state: TuiState, app: Any) -> None:
    asyncio.get_event_loop().create_task(_fetch_and_open(state, app))


async def _fetch_and_open(state: TuiState, app: Any) -> None:
    state.available_models = []
    state.show_model_selector = True
    app.invalidate()
    models = await _fetch_ollama_models()
    state.available_models = models
    if state.model_name in models:
        state.model_selector_idx = models.index(state.model_name)
    else:
        state.model_selector_idx = 0
    app.invalidate()


async def _fetch_ollama_models() -> list[str]:
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.get("http://localhost:11434/api/tags", timeout=5.0)
            return [f"ollama:{m['name']}" for m in r.json().get("models", [])]
    except Exception:  # noqa: BLE001
        return []


@registry.register("tropical", "Open tropical MCP inspector  /tropical [url]")
def _cmd_tropical(args: list[str], state: TuiState, app: Any) -> None:
    try:
        app._launch_tropical(args)
    except Exception as e:  # noqa: BLE001
        state.internal_log_lines.append(f"[ERR] tropical: failed to launch — {e}")
    state.active_panel = "internal_logs"
    app.invalidate()


@registry.register("q", "Quit the TUI")
def _cmd_quit(args: list[str], state: TuiState, app: Any) -> None:
    app.exit()
