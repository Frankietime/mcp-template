"""AgentTuiApp — thin TUI that subscribes to AgentSession.

Extends BaseTuiApp with:
- Dedicated _msg_queue so agent prompts don't block command handling
- /interpret command to launch beetle in a new terminal
- Log handler attachment for the agent's Python logging
- MCP session lifecycle (async with self._session)
"""

from __future__ import annotations

import asyncio
import subprocess
import tempfile

from prompt_toolkit.styles import Style

from tui.app import BaseTuiApp
from tui.state import TuiState

from .commands import registry as cmd_registry

from ..deps import AgentDeps
from ..session import AgentSession
from .log_handler import attach_log_handler, detach_log_handler

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
    "msg.tool":          "italic #5c2020",
    "msg.tool.done":     "#5c2020",
    "msg.cursor":        "#4a9eff",
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
})


class AgentTuiApp(BaseTuiApp):
    """Full-screen terminal UI for the pydantic-ai agent."""

    def __init__(self, session: AgentSession, deps: AgentDeps) -> None:
        state = TuiState(
            agent_name="lab_mouse",
            model_name=deps.model,
            username=deps.username,
            context_tokens_max=deps.context_window,
        )
        super().__init__(session, state, _STYLE, cmd_registry=cmd_registry)
        self._session: AgentSession  # narrow type for MCP context manager
        self._msg_queue: asyncio.Queue[str] = asyncio.Queue()

    # ------------------------------------------------------------------
    # Input routing

    def _send_message(self, text: str) -> None:
        """Send user messages to the agent-specific msg queue."""
        self._msg_queue.put_nowait(text)

    def _launch_beetle(self) -> None:
        """Write current logs to a temp file and open beetle in a new terminal."""
        tf = tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        )
        tf.write("\n".join(self._state.log_lines))
        tf.close()
        cmd = f'uv run beetle --logs "{tf.name}"'
        try:
            subprocess.Popen(["wt", "--", "cmd", "/k", cmd])
        except FileNotFoundError:
            subprocess.Popen(f"start cmd /k {cmd}", shell=True)  # noqa: S602

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
