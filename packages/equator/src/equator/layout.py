"""Layout factory — assembles the split-pane TUI layout.

Structure (top → bottom):
    ┌──────────────────────────────┐
    │ Title bar (agent name)       │  ← centered, 1 row
    ├──────────────────────────────┤
    │ [Help panel] │ Conversation  │  ← help sidebar (Tab) + history fill
    │              │  [Inspector]  │  ← inline below selected message (F2)
    ├──────────────────────────────┤  ← separator (always)
    │ Raw logs  (Ctrl+L)           │  ← shown when active_panel == "logs"
    ├──────────────────────────────┤
    │ Multi-line input (5 rows)    │
    ├──────────────────────────────┤
    │ Status bar (1 row)           │
    │ Context bar (1 row)          │
    └──────────────────────────────┘

A ``FloatContainer`` wraps the body so that the slash-command
``CompletionsMenu`` can appear as a floating dropdown anchored at the
cursor position inside the input area.
"""

from __future__ import annotations

from prompt_toolkit.application import get_app
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    Float,
    FloatContainer,
    HSplit,
    VSplit,
    Window,
)
from prompt_toolkit.layout.margins import ScrollbarMargin
from prompt_toolkit.widgets import Frame
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.menus import CompletionsMenu

from .components import ContextBarControl, HelpControl, HistoryControl, InputControl, LogsControl, ModelSelectorControl, StatusControl
from .state import TuiState

_LINE = "\u2500"  # ─


def _title_fragments(state: TuiState) -> StyleAndTextTuples:
    name = f" {state.agent_name or 'agent'} "
    try:
        width = get_app().output.get_size().columns
    except Exception:
        width = 80
    bar = max(0, width - len(name))
    left = bar // 2
    right = bar - left
    return [("class:title", _LINE * left + name + _LINE * right)]


def build_layout(
    state: TuiState,
    history: HistoryControl,
    input_ctrl: InputControl,
    status: StatusControl,
    logs: LogsControl,
    internal_logs: LogsControl,
    context_bar: ContextBarControl,
    model_selector: ModelSelectorControl,
    help_ctrl: HelpControl | None = None,
    detail: object | None = None,  # unused — inspector is rendered inline in history
) -> Layout:
    """Return a prompt_toolkit ``Layout`` for the agent TUI."""
    help_panel = ConditionalContainer(
        content=Window(
            content=help_ctrl or FormattedTextControl(lambda: []),
            width=26,
            style="class:help.bg",
        ),
        filter=Condition(lambda: state.show_help),
    )

    history_window = Window(
        content=history,
        wrap_lines=False,
        height=Dimension(min=3, weight=1),
        right_margins=[ScrollbarMargin(display_arrows=True)],
    )

    body = HSplit([
        Window(
            content=FormattedTextControl(lambda: _title_fragments(state)),
            height=1,
            align="center",
        ),
        VSplit([help_panel, history_window]),
        Window(height=1, char="\u2500"),
        ConditionalContainer(
            content=logs.container,
            filter=Condition(lambda: state.active_panel == "logs"),
        ),
        ConditionalContainer(
            content=internal_logs.container,
            filter=Condition(lambda: state.active_panel == "internal_logs"),
        ),
        Window(
            content=input_ctrl.buffer_control,
            height=5,
            wrap_lines=True,
            style="class:input-area",
        ),
        Window(content=status, height=1),
        context_bar.container,
    ])
    root = FloatContainer(
        content=body,
        floats=[
            Float(
                content=CompletionsMenu(max_height=8, scroll_offset=1),
                xcursor=True,
                ycursor=True,
            ),
            Float(
                content=ConditionalContainer(
                    content=Frame(
                        body=Window(content=model_selector, height=8),
                        title=" model ",
                        style="class:selector.frame",
                    ),
                    filter=Condition(lambda: state.show_model_selector),
                ),
                right=2,
                top=2,
                width=46,
            ),
        ],
    )
    return Layout(root, focused_element=input_ctrl.buffer_control)
