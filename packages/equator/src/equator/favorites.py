"""Persistence for favourite model names.

Stored as a JSON array at ``~/.config/mcp-agent/model_favorites.json``.
Reads and writes are synchronous — they happen only on explicit user action
(pressing ``*`` in the model selector), so blocking is not a concern.
"""

from __future__ import annotations

import json
from pathlib import Path

_PATH = Path.home() / ".config" / "mcp-agent" / "model_favorites.json"


def load() -> set[str]:
    """Return the persisted set of favourite model names (empty set on any error)."""
    try:
        data = json.loads(_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return set(data)
    except Exception:  # noqa: BLE001
        pass
    return set()


def save(favorites: set[str]) -> None:
    """Persist *favorites* to disk, creating parent directories as needed."""
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    _PATH.write_text(
        json.dumps(sorted(favorites), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
