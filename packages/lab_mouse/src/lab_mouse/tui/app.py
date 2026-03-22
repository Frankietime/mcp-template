"""AgentTuiApp — thin TUI that subscribes to AgentSession.

Extends BaseTuiApp with:
- Dedicated _msg_queue so agent prompts don't block command handling
- /beetle command to launch beetle in a new terminal
- Log handler attachment for the agent's Python logging
- MCP session lifecycle (async with self._session)
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import tempfile

from prompt_toolkit.styles import Style

from equator.app import BaseTuiApp
from equator.state import TuiState

from .commands import registry as cmd_registry

from ..deps import AgentDeps
from ..session import AgentSession
from .log_handler import _NAMED_LOGGERS, attach_log_handler, detach_log_handler

_STYLE = Style.from_dict({
    # Title bar
    "title":             "bold #ffffff",
    # Input area
    "input-area":        "bg:#1a1a2e #e0e0e0",
    # Log levels
    "log.dbg":           "ansibrightblack",
    "log.inf":           "#4a9eff",
    "log.wrn":           "#c8860a",
    "log.err":           "#c0392b",
    "log.crt":           "bold #8b0000",
    # Conversation history — left-border gutter pattern
    "msg.gutter.user":   "#555566",
    "msg.user":          "#b0b0c0",
    "msg.gutter.agent":  "#4a9eff",
    "msg.agent":         "#c8e8ff",
    "msg.agent.bold":    "bold #ffffff",
    "msg.tool":          "italic #5c2020",
    "msg.tool.done":     "#5c2020",
    "msg.cursor":        "#4a9eff",
    # Model selector overlay
    "selector.frame":    "bg:#1a1a2e #e0e0e0",
    "selector.item":     "#b0b0c0",
    "selector.selected": "bold #c8e8ff",
    "selector.empty":    "italic #4a4a5a",
    "selector.favorite": "bold #ffd700",
    # Status bar
    "status.model":      "bold #e0e0e0",
    "status.mcp.ok":     "#2d7a2d",
    "status.mcp.wait":   "#c8860a",
    "status.thinking":   "italic #c0392b",
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
    "help.header":         "bold #c8e8ff",
    "help.sep":            "#333344",
    "help.key":            "bold #4a9eff",
    "help.text":           "#888899",
})


class AgentTuiApp(BaseTuiApp):
    """Full-screen terminal UI for the pydantic-ai agent."""

    def __init__(self, session: AgentSession, deps: AgentDeps) -> None:
        state = TuiState(
            agent_name="lab_mouse",
            model_name=deps.model,
            username=deps.username,
            context_tokens_max=deps.context_window,
            mcp_server_url=deps.server_url,
            mcp_server_headers=deps.mcp_headers,
        )
        super().__init__(session, state, _STYLE, cmd_registry=cmd_registry)
        self._session: AgentSession  # narrow type for MCP context manager
        self._msg_queue: asyncio.Queue[str] = asyncio.Queue()
        self._beetle_handler: logging.Handler | None = None
        self._beetle_proc: subprocess.Popen | None = None
        self._beetle_tempfile: str | None = None

    # ------------------------------------------------------------------
    # Input routing

    def _send_message(self, text: str) -> None:
        """Send user messages to the agent-specific msg queue."""
        self._msg_queue.put_nowait(text)

    def _launch_beetle(self) -> None:
        """Launch beetle in a new terminal with log history pre-loaded and live forwarding active.

        Writes current logs to a temp file (history) and starts beetle with both
        ``--logs`` (pre-load) and ``--port`` (live TCP server).  Once beetle's
        server is ready, ``_attach_beetle_handler`` wires ``BeetleHandler`` into
        the Python logging pipeline so every future record is forwarded in real time.
        """
        if self._beetle_handler is not None:
            logging.getLogger(__name__).warning("beetle is already running — /beetle ignored")
            return

        from beetle.log_server import DEFAULT_PORT

        tf = tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        )
        tf.write("\n".join(self._state.log_lines))
        tf.close()

        cmd = f'uv run beetle --logs "{tf.name}" --port {DEFAULT_PORT}'
        self._beetle_tempfile = tf.name
        self._beetle_proc = subprocess.Popen(
            ["cmd", "/c", cmd], creationflags=subprocess.CREATE_NEW_CONSOLE
        )

        asyncio.create_task(self._attach_beetle_handler(DEFAULT_PORT))
        asyncio.create_task(self._monitor_beetle_proc(self._beetle_proc))

    async def _attach_beetle_handler(self, port: int) -> None:
        """Retry connecting BeetleHandler until beetle's TCP server is ready (~1 s boot)."""
        from beetle.log_server import BeetleHandler

        # Detach any previous handler from an earlier /beetle call
        if self._beetle_handler is not None:
            for name in _NAMED_LOGGERS:
                logging.getLogger(name).removeHandler(self._beetle_handler)
            self._beetle_handler.close()
            self._beetle_handler = None

        for _ in range(10):  # up to 5 s
            await asyncio.sleep(0.5)
            try:
                handler = BeetleHandler(port=port)
                handler.setLevel(logging.DEBUG)
                for name in _NAMED_LOGGERS:
                    logging.getLogger(name).addHandler(handler)
                self._beetle_handler = handler
                return
            except OSError:
                continue  # beetle not ready yet

    async def _monitor_beetle_proc(self, proc: subprocess.Popen) -> None:
        """Wait for the beetle process to exit, then detach the log handler.

        Runs in the background so that closing beetle from within its own TUI
        (e.g. /q or Ctrl+X) automatically cleans up lab_mouse's state and allows
        /beetle to be called again.
        """
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, proc.wait)
        if self._beetle_proc is not proc:
            return  # already replaced by a re-launch or killed by run() finally
        if self._beetle_handler is not None:
            for name in _NAMED_LOGGERS:
                logging.getLogger(name).removeHandler(self._beetle_handler)
            self._beetle_handler.close()
            self._beetle_handler = None
        self._beetle_proc = None
        self._beetle_tempfile = None

    # ------------------------------------------------------------------
    # Public

    async def run(self) -> None:
        """Start the TUI and all loops; blocks until the user quits."""
        unsubscribe = self._subscribe()
        log_handler, file_handler, beetle_handler = attach_log_handler(
            self._state,
            self._app,
            refresh_logs=self._logs_ctrl.refresh,
        )
        try:
            async with self._session:
                self._state.mcp_connected = True
                self._app.invalidate()
                await self._run_tasks()
        finally:
            unsubscribe()
            detach_log_handler(log_handler, file_handler, beetle_handler)
            if self._beetle_handler is not None:
                for name in _NAMED_LOGGERS:
                    logging.getLogger(name).removeHandler(self._beetle_handler)
                self._beetle_handler.close()
                self._beetle_handler = None
            if self._beetle_proc is not None:
                if self._beetle_tempfile:
                    # wt.exe exits immediately after opening the tab, so its PID
                    # is dead. Find the actual beetle process by its unique temp-file
                    # argument and kill it via PowerShell.
                    marker = self._beetle_tempfile.replace("'", "''")
                    subprocess.run(
                        [
                            "powershell", "-NoProfile", "-Command",
                            f"Get-CimInstance Win32_Process"
                            f" | Where-Object {{ $_.CommandLine -like '*{marker}*' }}"
                            f" | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }}",
                        ],
                        capture_output=True,
                    )
                    self._beetle_tempfile = None
                else:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(self._beetle_proc.pid)],
                        capture_output=True,
                    )
                self._beetle_proc = None
            self._terminate_tropical()

    def _handle_model_confirm(self) -> None:
        """Override: hot-swap the model on the session so the next prompt uses it."""
        if self._state.available_models:
            model = self._state.available_models[self._state.model_selector_idx]
            self._state.model_name = model
            self._session.set_model(model)
        self._state.show_model_selector = False
        self._app.invalidate()

    # ------------------------------------------------------------------
    # Coroutines

    async def _agent_loop(self) -> None:
        """Override: drain _msg_queue instead of base _queue."""
        while True:
            text = await self._msg_queue.get()
            spinner_task = asyncio.create_task(self._spin())
            try:
                await self._session.prompt(text)
            finally:
                spinner_task.cancel()


# Backward-compatible alias — existing code imports TuiApp
TuiApp = AgentTuiApp
