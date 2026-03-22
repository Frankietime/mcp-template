"""BeetleTuiApp — beetle chatbot TUI built on BaseTuiApp.

Extends BaseTuiApp with:
- 3-tuple queue (text, show_as_user_message, max_lines)
- Debounced auto-analysis when a log burst settles
- Optional log socket server and stdin pipe mode
"""

from __future__ import annotations

import asyncio
import os
import sys

from prompt_toolkit.styles import Style

from equator.app import BaseTuiApp
from equator.state import TuiState

from .commands import registry as cmd_registry

from .log_server import DEFAULT_PORT, log_server_loop
from .session import BeetleSession

_AUTO_PROMPT = "Briefly narrate what just happened in the latest logs. 2 sentences maximum."

_DEBOUNCE_SECONDS = 1.5

_STYLE = Style.from_dict({
    # Title bar
    "title":             "bold #ffffff",
    # Input area
    "input-area":        "bg:#1a1a2e #e0e0e0",
    # Log level tags (used by LogsControl's _LogLexer)
    "log.dbg":           "ansibrightblack",
    "log.inf":           "#4a9eff",
    "log.wrn":           "#c8860a",
    "log.err":           "#c0392b",
    "log.crt":           "bold #8b0000",
    # Conversation history — left-border gutter pattern
    "msg.gutter.user":   "#555566",
    "msg.user":          "#b0b0c0",
    "msg.gutter.agent":  "#2d7a2d",
    "msg.agent":         "#c8ffd4",
    "msg.agent.bold":    "bold #ffffff",
    "msg.tool":          "italic #4a4a00",
    "msg.tool.done":     "#4a4a00",
    "msg.cursor":        "#2d7a2d",
    # Model selector overlay
    "selector.frame":    "bg:#1a1a2e #e0e0e0",
    "selector.item":     "#b0b0c0",
    "selector.selected": "bold #c8ffd4",
    "selector.empty":    "italic #4a4a5a",
    # Status bar
    "status.model":      "bold #e0e0e0",
    "status.mcp.ok":     "#2d7a2d",
    "status.mcp.wait":   "#c8860a",
    "status.thinking":   "italic #2d7a2d",
    "status.hints":      "#4a4a5a",
    # Context window bar
    "ctx.low":           "#2d7a2d",
    "ctx.mid":           "#c8860a",
    "ctx.high":          "bold #8b0000",
    # JSON syntax in log panel
    "log.json":          "ansibrightblack",
    "log.json.key":      "#7ec8e3",
    "log.json.val":      "#b5cea8",
    # Logs pagination indicator
    "logs.page":         "bold #4a9eff",
    # Message detail view
    "msg.selected.gutter": "bold #c0392b",
    "msg.selected":        "bg:#3d0000 #ffcccc",
    "detail.bg":           "bg:#1a0008",
    "detail.header":       "bold #c0392b",
    "detail.key":          "#8b4444",
    "detail.val":          "#ffaaaa",
    "detail.empty":        "italic #4a4a5a",
    "detail.hint":         "italic #5a3030",
    # Help sidebar
    "help.bg":             "bg:#0d0d1a #888899",
    "help.header":         "bold #c8ffd4",
    "help.sep":            "#333344",
    "help.key":            "bold #4a9eff",
    "help.text":           "#888899",
})


class BeetleTuiApp(BaseTuiApp):
    """Standalone beetle chatbot application."""

    def __init__(
        self,
        session: BeetleSession,
        *,
        stdin_mode: bool = False,
        port: int | None = DEFAULT_PORT,
    ) -> None:
        state = TuiState(
            agent_name="beetle =){",
            log_lines=session._log_lines,
            model_name=os.getenv("BEETLE_MODEL", "ollama:phi4-mini"),
            username="((o))",
        )
        state.mcp_connected = True
        super().__init__(session, state, _STYLE, cmd_registry=cmd_registry)

        self._beetle_session = session
        self._stdin_mode = stdin_mode
        self._port = port
        # Override base _queue with beetle's 4-tuple shape: (text, show_user_msg, max_lines, mode)
        self._queue: asyncio.Queue[tuple[str, bool, int, str]] = asyncio.Queue()
        self._debounce_task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # Input routing

    def _send_message(self, text: str) -> None:
        """Put user messages into the beetle 4-tuple queue."""
        self._queue.put_nowait((text, False, 200, "explain"))

    # ------------------------------------------------------------------
    # Log line callback (shared by socket server and stdin loop)

    def _on_log_line(self) -> None:
        """Refresh the log panel and schedule a debounced auto-analysis."""
        self._logs_ctrl.refresh()
        self._app.invalidate()
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()
        self._debounce_task = asyncio.create_task(self._debounced_analyze())

    async def _debounced_analyze(self) -> None:
        """Wait for the log burst to settle, then queue an auto-analysis."""
        try:
            await asyncio.sleep(_DEBOUNCE_SECONDS)
            if self._queue.empty():
                self._queue.put_nowait((_AUTO_PROMPT, False, 30, "realtime"))
        except asyncio.CancelledError:
            pass

    # ------------------------------------------------------------------
    # Public

    async def run(self) -> None:
        """Start all tasks; populate the log panel if initial lines are present."""
        unsubscribe = self._subscribe()
        if self._beetle_session._log_lines:
            self._logs_ctrl.refresh()
        extra = []
        if self._stdin_mode:
            extra.append(self._stdin_loop())
        if self._port is not None:
            extra.append(log_server_loop(self._beetle_session, self._on_log_line, self._port))
        try:
            await self._run_tasks(*extra)
        finally:
            unsubscribe()

    # ------------------------------------------------------------------
    # Coroutines

    async def _agent_loop(self) -> None:
        """Override: drains the 4-tuple queue with per-call max_lines and mode."""
        while True:
            text, show_user_msg, max_lines, mode = await self._queue.get()
            if show_user_msg:
                self._history.add_user_message(text)
                self._app.invalidate()
            spinner_task = asyncio.create_task(self._spin())
            try:
                await self._session.prompt(
                    text,
                    max_lines=max_lines,
                    mode=mode,
                    active_levels=self._state.active_levels,
                )
            finally:
                spinner_task.cancel()

    def _handle_model_confirm(self) -> None:
        """Override: hot-swap the agent after updating the model name."""
        if self._state.available_models:
            model = self._state.available_models[self._state.model_selector_idx]
            self._state.model_name = model
            self._beetle_session.set_model(model)
        self._state.show_model_selector = False
        self._app.invalidate()

    async def _stdin_loop(self) -> None:
        """Read log lines from stdin (pipe mode) and append to the live buffer."""
        loop = asyncio.get_running_loop()
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:  # EOF
                break
            line = line.rstrip("\n")
            if line:
                self._beetle_session.append_line(line)
                self._on_log_line()
