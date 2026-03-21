# TOOL NAMES REGISTRY
#
# Centralizes all tool names as constants in a single file.
# This pattern provides:
# - Single source of truth: prevents name typos across features
# - Safe renames: change once, update everywhere via IDE refactor
# - Cross-tool references: use in error messages, NextAction hints, etc.
#
# Convention: snake_case names, action-first, domain-second
# Examples:
#   SEARCH_ATTRIBUTES = "search_audience_attributes"
#   CALCULATE_QUERY = "calculate_audience_query"


class ToolNames:
    """Centralized registry of MCP tool names."""

    TOOL_TEMPLATE = "mcp_tool_template"
    # Add more tool names here as new features are created
