"""TuiApp — lifecycle, agent loop, and state orchestration.

Two queues keep each concern independent:
- ``_cmd_queue`` — drained by ``_command_loop``, always responsive
- ``_msg_queue`` — drained by ``_agent_loop``, serialised MCP agent runs

Input is routed at submit time:
- ``/interpret``  → launches beetle in a new terminal window
- comma-commands  → ``_cmd_queue``
- main chat       → ``_msg_queue``

Panel transitions go through ``_set_panel()``, the single point that
updates ``state.active_panel``, moves keyboard focus, and invalidates.
"""

from __future__ import annotations

import asyncio
import subprocess
import tempfile

from prompt_toolkit import Application
from prompt_toolkit.styles import Style

from ..agent import create_agent
from ..deps import AgentDeps
from .commands import registry as cmd_registry
from .components import ContextBarControl, HistoryControl, InputControl, LogsControl, StatusControl
from .key_bindings import build_key_bindings
from .layout import build_layout
from .log_handler import attach_log_handler, detach_log_handler
from .state import ActivePanel, Message, TuiState
from .stream_handler import make_stream_handler

_SPINNER_INTERVAL = 0.125
_INTERPRET_COMMAND = "/interpret"

_STYLE = Style.from_dict({
    "input-area": "bg:#1a1a2e #e0e0e0",
    "log.dbg": "ansibrightblack",
    "log.inf": "ansiblue",
    "log.wrn": "ansiyellow",
    "log.err": "ansired",
    "log.crt": "bold ansired",
})


class TuiApp:
    """Full-screen terminal UI for the pydantic-ai agent."""

    def __init__(self, deps: AgentDeps) -> None:
        self._deps = deps
        self._state = TuiState(
            model_name=deps.model,
            username=deps.username,
            context_tokens_max=deps.context_window,
        )
        self._cmd_queue: asyncio.Queue[str] = asyncio.Queue()
        self._msg_queue: asyncio.Queue[str] = asyncio.Queue()
        self._pydantic_messages: list = []

        # Components
        self._history = HistoryControl(self._state)
        self._input_ctrl = InputControl(on_submit=self._route_input)
        self._status = StatusControl(self._state)
        self._logs_ctrl = LogsControl(self._state)
        self._context_bar = ContextBarControl(self._state)

        kb = build_key_bindings(
            on_quit=self._handle_quit,
            on_clear=self._handle_clear,
            on_toggle_logs=lambda: self._set_panel("main" if self._state.active_panel == "logs" else "logs"),
            on_cycle_panel=self._cycle_panel,
        )

        layout = build_layout(
            state=self._state,
            history=self._history,
            input_ctrl=self._input_ctrl,
            status=self._status,
            logs=self._logs_ctrl,
            context_bar=self._context_bar,
        )

        self._app: Application = Application(
            layout=layout,
            key_bindings=kb,
            style=_STYLE,
            full_screen=True,
        )

    # ------------------------------------------------------------------
    # Public

    async def run(self) -> None:
        """Start the TUI and all loops; blocks until the user quits."""
        agent = create_agent(self._deps)
        log_handler, file_handler = attach_log_handler(
            self._state,
            self._app,
            refresh_logs=self._logs_ctrl.refresh,
        )
        try:
            async with agent.run_mcp_servers():
                self._state.mcp_connected = True
                self._app.invalidate()
                await asyncio.gather(
                    self._app.run_async(),
                    self._command_loop(),
                    self._agent_loop(agent),
                    return_exceptions=True,
                )
        finally:
            detach_log_handler(log_handler, file_handler)

    # ------------------------------------------------------------------
    # Panel management

    def _set_panel(self, panel: ActivePanel) -> None:
        self._state.active_panel = panel
        self._app.layout.focus(self._input_ctrl.buffer_control)
        self._app.invalidate()

    # ------------------------------------------------------------------
    # Input routing

    def _route_input(self, text: str) -> None:
        """Route submitted text to the appropriate queue at submit time."""
        stripped = text.strip()
        if stripped == _INTERPRET_COMMAND:
            self._launch_beetle()
        elif cmd_registry.is_command(stripped):
            self._cmd_queue.put_nowait(stripped)
        else:
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
            subprocess.Popen(f"start cmd /k {cmd}", shell=True)

    # ------------------------------------------------------------------
    # Coroutines

    async def _command_loop(self) -> None:
        """Drain commands immediately — runs concurrently with the agent loop."""
        while True:
            text = await self._cmd_queue.get()
            cmd_registry.handle(text, self._state, self._app)
            self._logs_ctrl.refresh()
            self._app.layout.focus(self._input_ctrl.buffer_control)

    async def _agent_loop(self, agent) -> None:  # type: ignore[no-untyped-def]
        """Wait for user messages and drive pydantic-ai MCP agent runs."""
        while True:
            user_text = await self._msg_queue.get()

            self._state.messages.append(
                Message(role="user", content=user_text, complete=True)
            )
            self._state.thinking = True
            self._state.current_agent_text = ""
            self._app.invalidate()

            spinner_task = asyncio.create_task(self._spin())
            _output: str = ""

            try:
                handler = make_stream_handler(self._state, self._app)
                async with agent.run_stream(
                    user_text,
                    deps=self._deps,
                    message_history=self._pydantic_messages,
                    model=self._deps.model,
                    model_settings={"temperature": 0.1},
                    event_stream_handler=handler,
                ) as streamed:
                    result = await streamed.get_output()
                    if isinstance(result, str):
                        _output = result

                self._pydantic_messages = list(streamed.all_messages())
                usage = streamed.usage()
                if usage.total_tokens:
                    self._state.context_tokens_used = usage.total_tokens

            finally:
                spinner_task.cancel()
                self._state.thinking = False
                content = _output or self._state.current_agent_text
                if content:
                    self._state.messages.append(
                        Message(role="agent", content=content, complete=True)
                    )
                self._state.current_agent_text = ""
                self._app.invalidate()

    async def _spin(self) -> None:
        while True:
            await asyncio.sleep(_SPINNER_INTERVAL)
            self._status.tick()
            self._state.loader_frame += 1
            self._app.invalidate()

    # ------------------------------------------------------------------
    # Handlers

    def _cycle_panel(self) -> None:
        _ORDER: tuple[ActivePanel, ...] = ("main", "logs")
        current = self._state.active_panel
        next_panel = _ORDER[(_ORDER.index(current) + 1) % len(_ORDER)]
        self._set_panel(next_panel)

    def _handle_quit(self) -> None:
        self._app.exit()

    def _handle_clear(self) -> None:
        self._state.messages.clear()
        self._state.current_agent_text = ""
        self._app.invalidate()
