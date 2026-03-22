# tool_box/__init__.py
from fastmcp import FastMCP
from mcp_shared.config import Settings, get_settings


def register_all_tools(mcp: FastMCP, settings: Settings | None = None) -> None:
    """Register all MCP tools with the server instance.

    Each tool registration is gated behind its feature flag so tools can be
    enabled or disabled per environment without touching code.

    Add new tool registrations here as you create new features.
    Each feature should export a single add_tool(mcp) function.

    Pattern:
        from .my_feature.tools import add_tool as add_my_feature_tool

        if (settings or get_settings()).features.my_feature:
            add_my_feature_tool(mcp)
    """
    from .md_reader.tools import add_tool as add_md_reader_tool

    _settings = settings or get_settings()

    if _settings.features.md_reader:
        add_md_reader_tool(mcp)
