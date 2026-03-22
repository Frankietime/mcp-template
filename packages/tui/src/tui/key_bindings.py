"""Global key bindings with injected callbacks."""

from __future__ import annotations

from collections.abc import Callable

from prompt_toolkit.filters import has_completions
from prompt_toolkit.key_binding import KeyBindings


def build_key_bindings(
    on_quit: Callable[[], None],
    on_clear: Callable[[], None],
    on_show_logs: Callable[[], None],
    on_show_main: Callable[[], None],
) -> KeyBindings:
    """Build and return the global ``KeyBindings`` for the TUI.

    Args:
        on_quit: Called when the user presses ``Ctrl+X``.
        on_clear: Called when the user presses ``Ctrl+L``.
        on_show_logs: Called when the user presses ``Tab`` — switches to the raw logs panel.
            Suppressed when the completion dropdown is open (Tab selects completion instead).
        on_show_main: Called when the user presses ``Shift+Tab`` — switches to the
            interpretation (conversation) panel.
    """
    kb = KeyBindings()

    @kb.add("c-x")
    def _quit(event) -> None:  # type: ignore[no-untyped-def]
        on_quit()

    @kb.add("c-l")
    def _clear(event) -> None:  # type: ignore[no-untyped-def]
        on_clear()

    @kb.add("tab", filter=~has_completions)
    def _show_logs(event) -> None:  # type: ignore[no-untyped-def]
        on_show_logs()

    @kb.add("s-tab")
    def _show_main(event) -> None:  # type: ignore[no-untyped-def]
        on_show_main()

    return kb
