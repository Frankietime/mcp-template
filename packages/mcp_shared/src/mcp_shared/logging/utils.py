# mcp_shared/logging/utils.py
"""Tool execution tracking utilities."""

import functools
import time
from collections.abc import Callable, Coroutine
from typing import Any

from rich.console import Console

console = Console()


def record_tool_execution(tool_name: str, start_time: float, success: bool, error_type: str | None = None) -> None:
    """Record tool execution metrics.

    Args:
        tool_name: Name of the tool being executed
        start_time: Start time from time.perf_counter()
        success: Whether the tool executed successfully
        error_type: Type of error if not successful
    """
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    status = "OK" if success else error_type
    status_color = "green" if success else "red"
    console.print(
        f"[bold blue]Tool[/bold blue] [cyan]{tool_name}[/cyan]: "
        f"[yellow]{elapsed_ms:.0f}ms[/yellow] [[{status_color}]{status}[/{status_color}]]"
    )


def track_tool_execution(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
    """Decorator that wraps tool execution with timing and error tracking.

    Automatically uses the decorated function's name.

    Usage:
        @mcp.tool(...)
        @track_tool_execution
        async def my_tool(...):
            # just the business logic - no try/except/finally needed
            return result
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        success = True
        error_type = None
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            success = False
            error_type = type(e).__name__
            raise
        finally:
            record_tool_execution(func.__name__, start_time, success, error_type)

    return wrapper
