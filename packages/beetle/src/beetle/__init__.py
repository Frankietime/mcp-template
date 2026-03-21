"""Beetle (=){) — logs interpreter agent."""

from .agent import BEETLE_SYMBOL, build_beetle_prompt, create_beetle_agent
from .app import BeetleApp, DEFAULT_PROMPT, colorise

__all__ = [
    "BEETLE_SYMBOL",
    "build_beetle_prompt",
    "create_beetle_agent",
    "BeetleApp",
    "DEFAULT_PROMPT",
    "colorise",
]
