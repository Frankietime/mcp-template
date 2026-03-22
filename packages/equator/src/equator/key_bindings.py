"""Global key bindings with injected callbacks."""

from __future__ import annotations

from collections.abc import Callable

from prompt_toolkit.filters import Condition, has_completions
from prompt_toolkit.key_binding import KeyBindings


def build_key_bindings(
    on_quit: Callable[[], None],
    on_clear: Callable[[], None],
    on_show_logs: Callable[[], None],
    on_show_main: Callable[[], None],
    on_model_up: Callable[[], None],
    on_model_down: Callable[[], None],
    on_model_confirm: Callable[[], None],
    on_model_cancel: Callable[[], None],
    on_model_favorite: Callable[[], None],
    on_cursor_prev: Callable[[], None],
    on_cursor_next: Callable[[], None],
    on_log_page_back: Callable[[], None],
    on_log_page_forward: Callable[[], None],
    on_detail_toggle: Callable[[], None],
    on_detail_exit: Callable[[], None],
    on_detail_tool_prev: Callable[[], None],
    on_detail_tool_next: Callable[[], None],
    on_toggle_help: Callable[[], None],
    model_selector_open: Callable[[], bool],
    logs_panel_active: Callable[[], bool],
    detail_mode_active: Callable[[], bool],
    input_is_empty: Callable[[], bool],
    cursor_active: Callable[[], bool],
) -> KeyBindings:
    """Build and return the global ``KeyBindings`` for the TUI.

    Args:
        on_quit: ``Ctrl+X`` — exit the application.
        on_clear: No longer bound to a key; kept for API compatibility.
        on_show_logs: ``Ctrl+L`` — toggle the logs panel.
        on_show_main: ``Shift+Tab`` — toggle the internal-logs panel.
        on_model_up / on_model_down: Navigate model selector with arrow keys.
        on_model_confirm: Confirm model selection (``Enter`` when selector open).
        on_model_cancel: Dismiss model selector (``Escape`` when selector open).
        on_model_favorite: Toggle favourite on highlighted model (``*`` when selector open).
        on_cursor_prev / on_cursor_next: Navigate message cursor (Up/Down when input empty).
        on_log_page_back / on_log_page_forward: Paginate the logs panel.
        on_detail_toggle: Not bound; kept for API compatibility.
        on_detail_exit: ``Escape`` when cursor is active — clears the message cursor.
        on_detail_tool_prev / on_detail_tool_next: ``Left`` / ``Right`` when cursor active.
        on_toggle_help: ``Tab`` — toggle the left help sidebar.
        model_selector_open: Returns ``True`` when the model selector overlay is visible.
        logs_panel_active: Returns ``True`` when a logs panel is currently shown.
        detail_mode_active: Kept for API compatibility; no longer used for filtering.
        input_is_empty: Returns ``True`` when the input buffer has no text.
        cursor_active: Returns ``True`` when a message cursor is active in history.
    """
    kb = KeyBindings()
    selector_open = Condition(model_selector_open)
    logs_active = Condition(logs_panel_active)
    input_empty = Condition(input_is_empty)
    msg_cursor = Condition(cursor_active)

    @kb.add("c-x")
    def _quit(event) -> None:  # type: ignore[no-untyped-def]
        on_quit()

    # Ctrl+O: toggle logs panel
    @kb.add("c-o")
    def _show_logs(event) -> None:  # type: ignore[no-untyped-def]
        on_show_logs()

    # Tab: toggle help sidebar (only when no completions menu is open)
    @kb.add("tab", filter=~has_completions)
    def _toggle_help(event) -> None:  # type: ignore[no-untyped-def]
        on_toggle_help()

    # F2: toggle inspect/detail expansion
    @kb.add("f2")
    def _toggle_detail(event) -> None:  # type: ignore[no-untyped-def]
        on_detail_toggle()

    @kb.add("s-tab")
    def _show_main(event) -> None:  # type: ignore[no-untyped-def]
        on_show_main()

    # Model selector navigation
    @kb.add("up", filter=selector_open)
    def _model_up(event) -> None:  # type: ignore[no-untyped-def]
        on_model_up()

    @kb.add("down", filter=selector_open)
    def _model_down(event) -> None:  # type: ignore[no-untyped-def]
        on_model_down()

    @kb.add("enter", filter=selector_open, eager=True)
    def _model_confirm(event) -> None:  # type: ignore[no-untyped-def]
        on_model_confirm()

    @kb.add("escape", filter=selector_open, eager=True)
    def _model_cancel(event) -> None:  # type: ignore[no-untyped-def]
        on_model_cancel()

    @kb.add("*", filter=selector_open)
    def _model_favorite(event) -> None:  # type: ignore[no-untyped-def]
        on_model_favorite()

    # Message cursor — Up/Down when input is empty and no overlay is active
    @kb.add("up", filter=input_empty & ~selector_open, eager=True)
    def _cursor_up(event) -> None:  # type: ignore[no-untyped-def]
        on_cursor_prev()

    @kb.add("down", filter=input_empty & ~selector_open, eager=True)
    def _cursor_down(event) -> None:  # type: ignore[no-untyped-def]
        on_cursor_next()

    # Escape when cursor is active: clear cursor (return to auto-follow)
    @kb.add("escape", filter=msg_cursor & ~selector_open, eager=True)
    def _cursor_escape(event) -> None:  # type: ignore[no-untyped-def]
        on_detail_exit()

    # Tool call navigation — Left/Right when cursor active
    @kb.add("left", filter=msg_cursor & ~selector_open, eager=True)
    def _tool_prev(event) -> None:  # type: ignore[no-untyped-def]
        on_detail_tool_prev()

    @kb.add("right", filter=msg_cursor & ~selector_open, eager=True)
    def _tool_next(event) -> None:  # type: ignore[no-untyped-def]
        on_detail_tool_next()

    # Logs panel pagination — always available (no cursor, no selector)
    @kb.add("left", filter=~msg_cursor & ~selector_open, eager=True)
    def _log_page_back(event) -> None:  # type: ignore[no-untyped-def]
        on_log_page_back()

    @kb.add("right", filter=~msg_cursor & ~selector_open, eager=True)
    def _log_page_forward(event) -> None:  # type: ignore[no-untyped-def]
        on_log_page_forward()

    return kb
