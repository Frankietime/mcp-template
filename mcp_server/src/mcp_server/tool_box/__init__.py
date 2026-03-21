# tool_box/__init__.py
from fastmcp import FastMCP

from ._tools_template.tools import add_tool as add_template_tool


def register_all_tools(mcp: FastMCP) -> None:
    """Register all MCP tools with the server instance.

    Add new tool registrations here as you create new features.
    Each feature should export a single add_tool(mcp) function.

    Pattern:
        from .my_feature.tools import add_tool as add_my_feature_tool

        tools = [
            add_template_tool,
            add_my_feature_tool,
        ]
        for tool in tools:
            tool(mcp)
    """
    add_template_tool(mcp)
