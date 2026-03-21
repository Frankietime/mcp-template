"""Agent dependency container."""

from dataclasses import dataclass, field


@dataclass
class AgentDeps:
    """Runtime dependencies injected into the agent.

    Attributes:
        model: Pydantic-AI model string (e.g. ``"openai:gpt-4o"``).
        server_url: Base URL of the MCP server's SSE/HTTP endpoint.
        system_prompt: System instruction passed to the LLM on every run.
    """

    model: str = field(default="ollama:qwen3:4b")
    server_url: str = field(default="http://127.0.0.1:8000/mcp")
    system_prompt: str = field(default="/no_think You are a helpful assistant with access to MCP tools.")
