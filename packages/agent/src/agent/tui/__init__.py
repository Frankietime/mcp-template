"""Terminal UI for the agent."""

from __future__ import annotations


def __getattr__(name: str) -> object:
    if name == "TuiApp":
        from .app import TuiApp  # noqa: PLC0415
        return TuiApp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["TuiApp"]
