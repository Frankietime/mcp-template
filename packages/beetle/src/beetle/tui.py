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

# Crimson gradient palette (dark → light):
#   #0c0003  near-black crimson  — chat window + input bg (darkest)
#   #1a0008  very dark crimson   — secondary panels (detail, help)
#   #2d0010  dark crimson        — selector frame, gutters
#   #5c1020  deep crimson        — muted borders, hints
#   #8b1a2a  medium crimson      — secondary text, log.dbg
#   #c0392b  vivid crimson       — agent gutter, status ok, cursor
#   #dc143c  pure crimson        — titles, active selections
#   #ff4d6a  bright crimson      — agent text, emphasis
#   #ffaabb  pale rose           — light readout, detail.val

_STYLE = Style.from_dict({
    # Title bar
    "title":             "bold #dc143c",
    # Input area — darkest surface
    "input-area":        "bg:#0c0003 #8b1a2a",
    # Log level tags
    "log.dbg":           "#5c1020",
    "log.inf":           "#c0392b",
    "log.wrn":           "#d4622a",
    "log.err":           "#ff4d6a",
    "log.crt":           "bold #ff0033",
    # Conversation history — darkest bg via msg colors; gutter in crimson gradient
    "msg.gutter.user":   "#2d0010",
    "msg.user":          "#8b1a2a",
    "msg.gutter.agent":  "#c0392b",
    "msg.agent":         "#ff4d6a",
    "msg.agent.bold":    "bold #ffaabb",
    "msg.tool":          "italic #5c1020",
    "msg.tool.done":     "#8b1a2a",
    "msg.cursor":        "#dc143c",
    # Model selector overlay
    "selector.frame":    "bg:#2d0010 #c0392b",
    "selector.item":     "#8b1a2a",
    "selector.selected": "bold #ff4d6a",
    "selector.empty":    "italic #5c1020",
    "selector.favorite": "bold #ffd700",
    # Status bar
    "status.model":      "bold #ff4d6a",
    "status.mcp.ok":     "#c0392b",
    "status.mcp.wait":   "#d4622a",
    "status.thinking":   "italic #dc143c",
    "status.hints":      "#5c1020",
    # Context window bar
    "ctx.low":           "#8b1a2a",
    "ctx.mid":           "#c0392b",
    "ctx.high":          "bold #ff4d6a",
    # JSON syntax in log panel
    "log.json":          "#5c1020",
    "log.json.key":      "#c0392b",
    "log.json.val":      "#ff4d6a",
    # Logs pagination indicator
    "logs.page":         "bold #dc143c",
    # Message detail view — second darkest surface
    "msg.selected.gutter": "bold #dc143c",
    "msg.selected":        "bg:#2d0010 #ffaabb",
    "detail.bg":           "bg:#1a0008",
    "detail.header":       "bold #dc143c",
    "detail.key":          "#8b1a2a",
    "detail.val":          "#ffaabb",
    "detail.empty":        "italic #5c1020",
    "detail.hint":         "italic #2d0010",
    # Help sidebar — second darkest surface
    "help.bg":             "bg:#1a0008 #5c1020",
    "help.header":         "bold #dc143c",
    "help.sep":            "#2d0010",
    "help.key":            "bold #c0392b",
    "help.text":           "#5c1020",
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
            agent_name="beetle (~){",
            log_lines=session._log_lines,
            model_name=os.getenv("BEETLE_MODEL", "ollama:phi4-mini:3.8b"),
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
            self._terminate_tropical()

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
