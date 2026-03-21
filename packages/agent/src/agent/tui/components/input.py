"""Multi-line input control.

``Enter`` sends the message; ``Escape+Enter`` or ``Alt+Enter`` inserts a newline.
"""

from __future__ import annotations

from collections.abc import Callable

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.controls import BufferControl


class InputControl:
    """Wraps a prompt_toolkit ``Buffer`` for multi-line user input.

    Args:
        on_submit: Called with the buffer text when the user presses
            ``Enter``.  Typically ``asyncio.Queue.put_nowait``.
    """

    def __init__(self, on_submit: Callable[[str], None]) -> None:
        self._on_submit = on_submit
        self.buffer = Buffer(
            multiline=True,
            accept_handler=self._accept,
        )
        self.buffer_control = BufferControl(
            buffer=self.buffer,
            key_bindings=self._build_bindings(),
            focusable=True,
        )

    # ------------------------------------------------------------------
    # Internal

    def _accept(self, buf: Buffer) -> bool:
        text = buf.text
        if text.strip():
            self._on_submit(text)
        buf.reset()
        return True

    def _build_bindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("c-m")  # Enter → send
        @kb.add("c-j")  # Ctrl+Enter → send (same effect)
        def _submit(event) -> None:  # type: ignore[no-untyped-def]
            self.buffer.validate_and_handle()

        @kb.add("escape", "c-m")  # Escape+Enter → newline
        @kb.add("escape", "c-j")  # Escape+Ctrl+Enter → newline
        def _newline(event) -> None:  # type: ignore[no-untyped-def]
            self.buffer.insert_text("\n")

        return kb
