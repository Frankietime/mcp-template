"""BeetleApp — full-screen chatbot TUI for log interpretation.

Layout:
    ┌────────────────────────────────────────┐
    │  conversation history                  │  ← [USR]/[BTL]/[BTL_ERR] lines
    ├────────────────────────────────────────┤
    │  What are you looking for? =){  ___   │  ← single-line input
    └────────────────────────────────────────┘

On start:  if log lines are present, the default kick-start prompt is
           enqueued automatically so the user sees an analysis on arrival.
Controls:  Enter to submit, Ctrl+X / Ctrl+C to quit.
"""

from __future__ import annotations

import asyncio

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.styles import Style

from .agent import BEETLE_SYMBOL, build_beetle_prompt, create_beetle_agent

DEFAULT_PROMPT = "Show me the sequence of the most important logs so far"

_SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
_SPINNER_INTERVAL = 0.15

_GREEN = "\033[32m"
_CYAN = "\033[36m"
_CRIMSON = "\033[38;5;88m"
_RESET = "\033[0m"

_STYLE = Style.from_dict({
    "input-area": "bg:#1a1a2e #e0e0e0",
})

_LABEL: StyleAndTextTuples = [
    ("#8b0000", "What are you looking for? "),
    ("#2d7a2d bold", BEETLE_SYMBOL),
    ("#8b0000", "  "),
]
_LABEL_WIDTH = sum(len(t) for _, t in _LABEL)


def colorise(line: str) -> str:
    """Colour a beetle conversation line by its [TAG] prefix."""
    if not (line.startswith("[") and "]" in line):
        return line
    tag = line[1: line.index("]")]
    if tag == "USR":
        return f"{_CYAN}{line[len('[USR] '):]}{_RESET}"
    if tag == "BTL":
        return f"{_GREEN}{BEETLE_SYMBOL}{_RESET} {line[len('[BTL] '):]}"
    if tag == "BTL_ERR":
        return f"{_CRIMSON}[BTL_ERR] {line[len('[BTL_ERR] '):]}{_RESET}"
    return line


class BeetleApp:
    """Standalone beetle chatbot application."""

    def __init__(self, log_lines: list[str]) -> None:
        self._log_lines = log_lines
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._conv_lines: list[str] = []
        self._loader_frame: int = 0

        self._history_buf = Buffer(multiline=True, name="history")
        self._input_buf = Buffer(multiline=False, accept_handler=self._accept)

        kb = KeyBindings()

        @kb.add("c-m")
        @kb.add("c-j")
        def _submit(event) -> None:  # type: ignore[no-untyped-def]
            self._input_buf.validate_and_handle()

        @kb.add("c-x")
        @kb.add("c-c")
        def _quit(event) -> None:  # type: ignore[no-untyped-def]
            event.app.exit()

        input_ctrl = BufferControl(
            buffer=self._input_buf,
            key_bindings=kb,
            focusable=True,
        )

        layout = Layout(
            HSplit([
                Window(
                    content=BufferControl(buffer=self._history_buf, focusable=False),
                    height=Dimension(min=3, weight=1),
                    wrap_lines=True,
                    allow_scroll_beyond_bottom=True,
                ),
                Window(height=1, char="\u2500"),
                VSplit([
                    Window(
                        content=FormattedTextControl(_LABEL),
                        width=_LABEL_WIDTH,
                        height=1,
                        style="class:input-area",
                    ),
                    Window(
                        content=input_ctrl,
                        height=1,
                        wrap_lines=False,
                        style="class:input-area",
                    ),
                ]),
            ]),
            focused_element=input_ctrl,
        )

        self._app = Application(
            layout=layout,
            style=_STYLE,
            full_screen=True,
        )

    def _accept(self, buf: Buffer) -> bool:
        text = buf.text.strip()
        if text:
            self._conv_lines.append(f"[USR] {text}")
            self._refresh()
            self._queue.put_nowait(text)
        buf.reset()
        return True

    def _refresh(self) -> None:
        lines = [colorise(line) for line in self._conv_lines]
        text = "\n".join(lines)
        self._history_buf.set_document(Document(text=text, cursor_position=len(text)))

    async def run(self) -> None:
        """Start the chatbot; auto-runs kick-start if log lines are present."""
        if self._log_lines:
            self._queue.put_nowait(DEFAULT_PROMPT)
        await asyncio.gather(
            self._app.run_async(),
            self._agent_loop(),
            return_exceptions=True,
        )

    async def _agent_loop(self) -> None:
        beetle = create_beetle_agent()
        while True:
            intention = await self._queue.get()
            spinner_task = asyncio.create_task(self._spin())
            try:
                prompt = build_beetle_prompt(self._log_lines, intention)
                result = await beetle.run(prompt)
                response = result.output if hasattr(result, "output") else str(result.data)
                self._conv_lines.append(f"[BTL] {response}")
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                self._conv_lines.append(f"[BTL_ERR] {exc}")
            finally:
                spinner_task.cancel()
                self._refresh()
                self._app.invalidate()

    async def _spin(self) -> None:
        while True:
            await asyncio.sleep(_SPINNER_INTERVAL)
            self._loader_frame += 1
            self._app.invalidate()
