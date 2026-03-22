"""Beetle-specific slash commands.

Extends the shared TUI registry with beetle-specific context in /help.
Beetle commands: /help, /logs, /q  (all from base registry).

The /help output adds a beetle-specific footer explaining auto-analysis
and the two response modes (realtime vs explain).
"""

from __future__ import annotations

from typing import Any

from equator.commands import CommandRegistry, TuiState, registry as _base_registry

registry = _base_registry.extend()


@registry.register("help", "Show key bindings, commands, and beetle modes")
def _cmd_help_beetle(args: list[str], state: TuiState, app: Any) -> None:
    """Beetle-flavoured /help — delegates to base then appends beetle context."""
    # Delegate to base help (reads app.cmd_registry for the command list)
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
        "[INF] help:   Enter          Ask beetle about the logs",
        "[INF] help:   Esc+Enter      Insert newline",
        "[INF] help:   Ctrl+O         Toggle logs panel  (raw stream)",
        "[INF] help:   Tab            Toggle help sidebar",
        "[INF] help:   F2             Toggle inspect expansion",
        "[INF] help:   Shift+Tab      Toggle internal logs",
        "[INF] help:   ↑ ↓            Navigate messages (when input empty)",
        "[INF] help:   ← →            Cycle tool calls in selected message",
        "[INF] help:   Esc            Clear message cursor",
        "[INF] help:   Ctrl+X         Quit",
        "[INF] help: ──────────────────────────────────────────",
        "[INF] help:   How beetle works",
        "[INF] help: ──────────────────────────────────────────",
        "[INF] help:   Auto-analysis  Runs after log bursts settle (1.5 s debounce)",
        "[INF] help:   realtime mode  One sentence — used for auto-analysis",
        "[INF] help:   explain mode   Flow chain — used for your questions",
        "[INF] help:   /logs [lvl]    Filter which levels beetle sees",
        "[INF] help: ══════════════════════════════════════════",
    ]
    state.internal_log_lines.extend(lines)
    state.active_panel = "internal_logs"
    app.invalidate()


