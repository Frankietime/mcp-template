"""Beetle (=){) — logs interpreter agent."""

from .agent import BEETLE_SYMBOL, build_beetle_prompt, create_beetle_agent
from .commands import registry as cmd_registry
from .log_filter import NoiseRuleEntry, filter_for_context, is_noise
from .log_server import BeetleHandler, DEFAULT_PORT
from .session import BeetleSession
from .tui import BeetleTuiApp

__all__ = [
    "BEETLE_SYMBOL",
    "build_beetle_prompt",
    "cmd_registry",
    "create_beetle_agent",
    "BeetleHandler",
    "BeetleSession",
    "BeetleTuiApp",
    "DEFAULT_PORT",
    "is_noise",
    "filter_for_context",
    "NoiseRuleEntry",
]
