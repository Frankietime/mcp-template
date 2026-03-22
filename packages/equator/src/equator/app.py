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
from .components import ContextBarControl, DetailControl, HelpControl, HistoryControl, InputControl, LogsControl, ModelSelectorControl, StatusControl
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


def _set_terminal_title(title: str) -> None:
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(title)  # type: ignore[attr-defined]
        except Exception:
            pass
    else:
        sys.stdout.write(f"\033]0;{title}\007")
        sys.stdout.flush()


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
        self._token_snapshot: int = 0

        completer = SlashCompleter(cmd_registry) if cmd_registry else None
        self._input_ctrl = InputControl(on_submit=self._route_input, completer=completer)
        self._status = StatusControl(state)
        self._logs_ctrl = LogsControl(state.log_lines, name="logs")
        self._internal_logs_ctrl = LogsControl(state.internal_log_lines, name="internal_logs")
        self._context_bar = ContextBarControl(state)
        self._model_selector = ModelSelectorControl(state)
        self._detail_ctrl = DetailControl(self._history)
        self._help_ctrl = HelpControl(state)

        kb = build_key_bindings(
            on_quit=self._handle_quit,
            on_clear=self._handle_clear,
            on_show_logs=self._handle_show_logs,
            on_show_main=self._handle_show_main,
            on_model_up=self._handle_model_up,
            on_model_down=self._handle_model_down,
            on_model_confirm=self._handle_model_confirm,
            on_model_cancel=self._handle_model_cancel,
            on_cursor_prev=self._handle_cursor_prev,
            on_cursor_next=self._handle_cursor_next,
            on_log_page_back=self._handle_log_page_back,
            on_log_page_forward=self._handle_log_page_forward,
            on_detail_toggle=self._handle_detail_toggle,
            on_detail_exit=self._handle_detail_exit,
            on_detail_tool_prev=self._handle_detail_tool_prev,
            on_detail_tool_next=self._handle_detail_tool_next,
            on_toggle_help=self._handle_toggle_help,
            model_selector_open=lambda: self._state.show_model_selector,
            logs_panel_active=lambda: self._state.active_panel in ("logs", "internal_logs"),
            detail_mode_active=lambda: self._state.detail_mode,
            input_is_empty=lambda: not self._input_ctrl.buffer.text,
            cursor_active=lambda: self._history.cursor_active,
        )
        layout = build_layout(
            state=state,
            history=self._history,
            input_ctrl=self._input_ctrl,
            status=self._status,
            logs=self._logs_ctrl,
            internal_logs=self._internal_logs_ctrl,
            context_bar=self._context_bar,
            model_selector=self._model_selector,
            help_ctrl=self._help_ctrl,
            detail=self._detail_ctrl,
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
                return  # _spin redraws at 8 fps during streaming — no per-token invalidate
            case ToolCallEvent(name=n, args=a):
                self._history.add_tool_call(n, a)
            case ToolResultEvent(result=r):
                self._history.complete_last_tool(r)
            case AgentStartEvent(agent_id=aid):
                self._history.start_agent_stream(aid)
                self._state.thinking = True
                self._token_snapshot = self._state.context_tokens_used
            case AgentEndEvent(output=out):
                self._history.end_agent_stream(out)
                self._state.thinking = False
                if not self._state.detail_mode:
                    self._history.follow_latest()
            case TokenUsageEvent(total=t):
                delta = t - self._token_snapshot
                self._token_snapshot = t
                self._history.receive_tokens(delta)
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
        app-specific commands (e.g. /beetle in AgentTuiApp).
        """
        stripped = text.strip()
        if not stripped:
            return
        if self._cmd_registry and self._cmd_registry.is_command(stripped):
            self._dispatch_command(stripped)
            return
        self._history.add_user_message(stripped)
        if not self._state.detail_mode:
            self._history.follow_latest()
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

    def _handle_show_logs(self) -> None:
        self._set_panel("main" if self._state.active_panel == "logs" else "logs")

    def _handle_show_main(self) -> None:
        self._set_panel("main" if self._state.active_panel == "internal_logs" else "internal_logs")

    def _handle_toggle_help(self) -> None:
        self._state.show_help = not self._state.show_help
        self._app.invalidate()

    def _handle_quit(self) -> None:
        self._app.exit()

    def _handle_clear(self) -> None:
        self._session.clear()

    def _handle_model_up(self) -> None:
        if self._state.available_models:
            n = len(self._state.available_models)
            self._state.model_selector_idx = (self._state.model_selector_idx - 1) % n
            self._app.invalidate()

    def _handle_model_down(self) -> None:
        if self._state.available_models:
            n = len(self._state.available_models)
            self._state.model_selector_idx = (self._state.model_selector_idx + 1) % n
            self._app.invalidate()

    def _handle_model_cancel(self) -> None:
        self._state.show_model_selector = False
        self._app.invalidate()

    def _handle_model_confirm(self) -> None:
        """Select the highlighted model. Subclasses override to also hot-swap the agent."""
        if self._state.available_models:
            self._state.model_name = self._state.available_models[self._state.model_selector_idx]
        self._state.show_model_selector = False
        self._app.invalidate()

    def _handle_cursor_prev(self) -> None:
        self._history.cursor_prev()
        self._app.invalidate()

    def _handle_cursor_next(self) -> None:
        self._history.cursor_next()
        self._app.invalidate()

    def _handle_detail_toggle(self) -> None:
        if self._state.detail_mode:
            self._history.exit_detail()
        else:
            self._history.enter_detail()
        self._app.invalidate()

    def _handle_detail_exit(self) -> None:
        self._history.follow_latest()
        self._app.invalidate()

    def _handle_detail_tool_prev(self) -> None:
        self._history.detail_tool_prev()
        self._app.invalidate()

    def _handle_detail_tool_next(self) -> None:
        self._history.detail_tool_next()
        self._app.invalidate()

    def _handle_log_page_back(self) -> None:
        active = self._state.active_panel
        ctrl = self._logs_ctrl if active == "logs" else self._internal_logs_ctrl
        ctrl.page_back()
        self._app.invalidate()

    def _handle_log_page_forward(self) -> None:
        active = self._state.active_panel
        ctrl = self._logs_ctrl if active == "logs" else self._internal_logs_ctrl
        ctrl.page_forward()
        self._app.invalidate()

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
        _set_terminal_title(self._state.agent_name)
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
