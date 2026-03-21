"""Global key bindings with injected callbacks."""

from __future__ import annotations

from collections.abc import Callable

from prompt_toolkit.key_binding import KeyBindings


def build_key_bindings(
    on_quit: Callable[[], None],
    on_clear: Callable[[], None],
    on_toggle_logs: Callable[[], None],
    on_cycle_panel: Callable[[], None],
) -> KeyBindings:
    """Build and return the global ``KeyBindings`` for the TUI.

    Args:
        on_quit: Called when the user presses ``Ctrl+X``.
        on_clear: Called when the user presses ``Ctrl+L``.
        on_toggle_logs: Called when the user presses ``Ctrl+P``.
        on_cycle_panel: Called when the user presses ``Tab`` — cycles main→logs→main.
    """
    kb = KeyBindings()

    @kb.add("c-x")
    def _quit(event) -> None:  # type: ignore[no-untyped-def]
        on_quit()

    @kb.add("c-l")
    def _clear(event) -> None:  # type: ignore[no-untyped-def]
        on_clear()

    @kb.add("c-p")
    def _toggle_logs(event) -> None:  # type: ignore[no-untyped-def]
        on_toggle_logs()

    @kb.add("tab")
    def _cycle(event) -> None:  # type: ignore[no-untyped-def]
        on_cycle_panel()

    return kb
