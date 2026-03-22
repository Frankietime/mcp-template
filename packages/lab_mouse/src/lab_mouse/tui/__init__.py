"""Terminal UI for the agent."""

from __future__ import annotations


def __getattr__(name: str) -> object:
    if name in ("TuiApp", "AgentTuiApp"):
        from .app import AgentTuiApp  # noqa: PLC0415
        return AgentTuiApp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["AgentTuiApp", "TuiApp"]
