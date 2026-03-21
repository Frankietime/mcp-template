"""Docstring Registry for tool_template tools.

Usage:
    from .docstrings import DOCSTRINGS

    @mcp.tool(description=DOCSTRINGS["tool_template"])
    async def tool_template(...):
        pass
"""

from .tool_template_docs import TOOL_TEMPLATE_V1, TOOL_TEMPLATE_V2

# Register active docstrings here
DOCSTRINGS = {
    "tool_template": TOOL_TEMPLATE_V1,  # Switch to TOOL_TEMPLATE_V2 when ready
}

__all__ = ["DOCSTRINGS", "TOOL_TEMPLATE_V1", "TOOL_TEMPLATE_V2"]
