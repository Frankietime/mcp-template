"""BaseTuiApp — full TUI backbone shared by agent and beetle.

Owns component creation, layout, key bindings, Application, and the
shared async loops (_agent_loop, _spin, _run_tasks).  Subclasses
supply their own _STYLE, override _send_message / _agent_loop when
needed, and implement run() to add session lifecycle logic.
"""

from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import Callable, Coroutine
from typing import Any

from prompt_toolkit import Application
from prompt_toolkit.document import Document
from prompt_toolkit.styles import Style

from .commands import CommandKind, CommandRegistry, SlashCompleter
from .components import ContextBarControl, HistoryControl, InputControl, LogsControl, StatusControl
from .key_bindings import build_key_bindings
from .layout import build_layout
from .protocol import (
    AgentEndEvent,
    AgentStartEvent,
    ClearedEvent,
    SessionEvent,
    SessionProtocol,
    TextDeltaEvent,
    TokenUsageEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from .state import ActivePanel, TuiState

_SPINNER_INTERVAL = 0.125


class BaseTuiApp:
    """Wires a SessionProtocol to a prompt_toolkit Application.

    Subclasses override _send_message for custom queue shapes (e.g. the
    beetle 3-tuple), override _route_input to intercept special commands
    before calling super(), and implement run() to add session lifecycle
    (MCP handshake, log handlers, extra coroutines).
    """

    def __init__(
        self,
        session: SessionProtocol,
        state: TuiState,
        style: Style,
        cmd_registry: CommandRegistry | None = None,
    ) -> None:
        self._session = session
        self._state = state
        self._cmd_registry = cmd_registry
        self._history = HistoryControl(state)
        self._queue: asyncio.Queue[str] = asyncio.Queue()

        completer = SlashCompleter(cmd_registry) if cmd_registry else None
        self._input_ctrl = InputControl(on_submit=self._route_input, completer=completer)
        self._status = StatusControl(state)
        self._logs_ctrl = LogsControl(state.log_lines, name="logs")
        self._internal_logs_ctrl = LogsControl(state.internal_log_lines, name="internal_logs")
        self._context_bar = ContextBarControl(state)

        kb = build_key_bindings(
            on_quit=self._handle_quit,
            on_clear=self._handle_clear,
            on_show_logs=lambda: self._set_panel("main" if self._state.active_panel == "logs" else "logs"),
            on_show_main=lambda: self._set_panel("main" if self._state.active_panel == "internal_logs" else "internal_logs"),
        )
        layout = build_layout(
            state=state,
            history=self._history,
            input_ctrl=self._input_ctrl,
            status=self._status,
            logs=self._logs_ctrl,
            internal_logs=self._internal_logs_ctrl,
            context_bar=self._context_bar,
        )
        output = None
        if sys.platform == "win32" and os.environ.get("TERM"):
            try:
                from prompt_toolkit.output.vt100 import Vt100_Output
                output = Vt100_Output.from_pty(sys.stdout, term=os.environ["TERM"])
            except Exception:
                pass

        self._app = Application(
            layout=layout,
            key_bindings=kb,
            style=style,
            full_screen=True,
            output=output,
        )

    # ------------------------------------------------------------------
    # Subscription

    def _subscribe(self) -> Callable[[], None]:
        """Subscribe to session events. Returns an unsubscribe callable."""
        return self._session.subscribe(self._handle_event)

    def _handle_event(self, event: SessionEvent) -> None:
        """Single mutation point — all component/state changes happen here."""
        match event:
            case TextDeltaEvent(content=c):
                self._history.append_delta(c)
            case ToolCallEvent(name=n):
                self._history.add_tool_call(n)
            case ToolResultEvent():
                self._history.complete_last_tool()
            case AgentStartEvent(agent_id=aid):
                self._history.start_agent_stream(aid)
                self._state.thinking = True
            case AgentEndEvent(output=out):
                self._history.end_agent_stream(out)
                self._state.thinking = False
            case TokenUsageEvent(total=t):
                self._state.context_tokens_used = t
            case ClearedEvent():
                self._history.clear()
                self._state.thinking = False
        self._app.invalidate()

    # ------------------------------------------------------------------
    # Panel management

    def _set_panel(self, panel: ActivePanel) -> None:
        self._state.active_panel = panel
        self._app.layout.focus(self._input_ctrl.buffer_control)
        self._app.invalidate()

    def _cycle_panel(self) -> None:
        panels: tuple[ActivePanel, ...] = ("main", "logs")
        current = self._state.active_panel
        self._set_panel(panels[(panels.index(current) + 1) % len(panels)])

    # ------------------------------------------------------------------
    # Input routing

    def _route_input(self, text: str) -> None:
        """Route submitted text: handle slash commands or forward to the agent.

        Subclasses may call super()._route_input(text) after intercepting
        app-specific commands (e.g. /interpret in AgentTuiApp).
        """
        stripped = text.strip()
        if not stripped:
            return
        if self._cmd_registry and self._cmd_registry.is_command(stripped):
            self._dispatch_command(stripped)
            return
        self._history.add_user_message(stripped)
        self._app.invalidate()
        self._send_message(stripped)

    def _dispatch_command(self, text: str) -> None:
        """Handle a recognised slash-command string.

        Passes ``self`` as the ``app`` argument to command handlers so they
        can call ``app.exit()``, ``app.invalidate()``, ``app.cmd_registry``,
        or any subclass-specific method (e.g. ``app._launch_beetle()``).
        """
        from .commands import PREFIX
        parts = text[len(PREFIX):].strip().lower().split()
        name = parts[0] if parts else ""
        cmd = self._cmd_registry.get(name) if self._cmd_registry else None  # type: ignore[union-attr]
        if cmd is None:
            if self._cmd_registry:
                self._cmd_registry.handle(text, self._state, self)
            self._logs_ctrl.refresh()
            self._internal_logs_ctrl.refresh()
            self._app.layout.focus(self._input_ctrl.buffer_control)
            return
        match cmd.kind:
            case CommandKind.ACTION:
                if self._cmd_registry:
                    self._cmd_registry.handle(text, self._state, self)
                self._logs_ctrl.refresh()
                self._internal_logs_ctrl.refresh()
                self._app.layout.focus(self._input_ctrl.buffer_control)
            case CommandKind.PROMPT:
                if cmd.template:
                    self._input_ctrl.buffer.set_document(
                        Document(text=cmd.template, cursor_position=len(cmd.template))
                    )
            case CommandKind.SCRIPT:
                if cmd.template:
                    self._history.add_user_message(cmd.template)
                    self._app.invalidate()
                    self._send_message(cmd.template)

    # ------------------------------------------------------------------
    # Command-handler interface (called by command fns via the ``app`` arg)

    @property
    def cmd_registry(self) -> CommandRegistry | None:
        """The registry passed to this app; exposed so /help can list all commands."""
        return self._cmd_registry

    def exit(self) -> None:
        """Exit the application."""
        self._app.exit()

    def invalidate(self) -> None:
        """Trigger a UI redraw."""
        self._app.invalidate()

    def _send_message(self, text: str) -> None:
        """Enqueue a user message for the agent loop.

        Override in subclasses that use a different queue shape
        (e.g. BeetleTuiApp uses a 3-tuple).
        """
        self._queue.put_nowait(text)

    # ------------------------------------------------------------------
    # Handlers

    def _handle_quit(self) -> None:
        self._app.exit()

    def _handle_clear(self) -> None:
        self._session.clear()

    # ------------------------------------------------------------------
    # Coroutines

    async def _agent_loop(self) -> None:
        """Default loop: drain str queue, spin, call session.prompt."""
        while True:
            text = await self._queue.get()
            spinner_task = asyncio.create_task(self._spin())
            try:
                await self._session.prompt(text)
            finally:
                spinner_task.cancel()

    async def _spin(self) -> None:
        while True:
            await asyncio.sleep(_SPINNER_INTERVAL)
            self._status.tick()
            self._state.loader_frame += 1
            self._app.invalidate()

    async def _run_tasks(self, *extra_coros: Coroutine[Any, Any, None]) -> None:
        """Run app + agent_loop + any extra coroutines; cancel all on first exit."""
        tasks = [
            asyncio.create_task(self._app.run_async()),
            asyncio.create_task(self._agent_loop()),
            *[asyncio.create_task(c) for c in extra_coros],
        ]
        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for t in tasks:
                t.cancel()
            results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, BaseException) and not isinstance(r, (asyncio.CancelledError, KeyboardInterrupt)):
                raise r
