"""Structured output schemas for the agent."""

from pydantic import BaseModel


class AgentResult(BaseModel):
    """Structured output returned by the agent after each run.

    Attributes:
        response: The agent's natural-language reply.
        tool_calls_made: Number of MCP tool calls executed during the run.
    """

    response: str
    tool_calls_made: int = 0
