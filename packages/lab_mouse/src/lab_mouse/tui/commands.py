"""Lab-mouse-specific slash commands.

Extends the shared TUI registry with agent-specific commands:
    /interpret  Open beetle in a new terminal to analyse the current logs
"""

from __future__ import annotations

from typing import Any

from tui.commands import TuiState, registry as _base_registry

registry = _base_registry.extend()


@registry.register("interpret", "Open beetle in a new terminal")
def _cmd_interpret(args: list[str], state: TuiState, app: Any) -> None:
    app._launch_beetle()
