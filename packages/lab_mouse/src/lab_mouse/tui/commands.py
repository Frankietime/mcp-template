"""Lab-mouse-specific slash commands.

Extends the shared TUI registry with agent-specific commands:
    /beetle  Launch beetle in a new terminal with live log forwarding
"""

from __future__ import annotations

from typing import Any

from equator.commands import TuiState, registry as _base_registry

registry = _base_registry.extend()


@registry.register("beetle", "Launch beetle in a new terminal with live log forwarding")
def _cmd_beetle(args: list[str], state: TuiState, app: Any) -> None:
    app._launch_beetle()
