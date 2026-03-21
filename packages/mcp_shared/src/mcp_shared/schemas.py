# mcp_shared/schemas.py
"""Shared schemas and enums for MCP tools."""

from enum import Enum

from pydantic import BaseModel


class ResponseFormat(Enum):
    """Controls tool output verbosity.

    Use this enum as a tool argument to let agents select
    the level of detail they need from tool responses.

    - CONCISE: Minimal response with essential summary only
    - DETAILED: Standard response with data preview, highlights, next steps
    - VERBOSE_DEBUG: Full response including debug info, token counts, all sections
    """

    CONCISE = "concise"
    DETAILED = "detailed"
    VERBOSE_DEBUG = "verbose_debug"


# region Generic Output Models
# These are example output models for use in tool templates.
# Replace with your domain-specific models when building a real MCP server.

class ResourceModel(BaseModel):
    """Generic resource model — replace with your domain model."""

    id: int
    name: str
    status: str
    metadata: dict = {}


class ItemModel(BaseModel):
    """Generic item model — replace with your domain model."""

    id: int
    label: str
    value: float
    tags: list[str] = []

# endregion
