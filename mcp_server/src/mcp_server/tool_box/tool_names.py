# TOOL NAMES REGISTRY
#
# Centralizes all tool names as constants in a single file.
# This pattern provides:
# - Single source of truth: prevents name typos across features
# - Safe renames: change once, update everywhere via IDE refactor
# - Cross-tool references: use in error messages, NextStep hints, etc.
#
# Convention: snake_case names, action-first, domain-second
# Examples:
#   LIST_RESOURCES = "list_resources"
#   GET_RESOURCE_BY_ID = "get_resource_by_id"
#   CREATE_RESOURCE = "create_resource"


class ToolNames:
    """Centralized registry of all MCP tool names."""

    # Add your tool name constants here as you create new tools.
    # Import this class wherever you need to reference a tool by name.
