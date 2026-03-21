"""Layout factory — assembles the split-pane TUI layout.

Structure (top → bottom):
    ┌──────────────────────────────┐
    │ Conversation history         │  ← fills remaining height
    ├──────────────────────────────┤  ← separator (always)
    │ Raw logs  (,1)               │  ← shown when active_panel == "logs"
    ├──────────────────────────────┤
    │ Multi-line input (5 rows)    │
    ├──────────────────────────────┤
    │ Status bar (1 row)           │
    │ Context bar (1 row)          │
    └──────────────────────────────┘
"""

from __future__ import annotations

from prompt_toolkit.filters import Condition
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import ConditionalContainer, HSplit, Window
from prompt_toolkit.layout.dimension import Dimension

from .components import ContextBarControl, HistoryControl, InputControl, LogsControl, StatusControl
from .state import TuiState


def build_layout(
    state: TuiState,
    history: HistoryControl,
    input_ctrl: InputControl,
    status: StatusControl,
    logs: LogsControl,
    context_bar: ContextBarControl,
) -> Layout:
    """Return a prompt_toolkit ``Layout`` for the agent TUI."""
    body = HSplit([
        Window(content=history, wrap_lines=True, height=Dimension(min=3, weight=1)),
        Window(height=1, char="\u2500"),
        ConditionalContainer(
            content=logs.container,
            filter=Condition(lambda: state.active_panel == "logs"),
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
    return Layout(body, focused_element=input_ctrl.buffer_control)
