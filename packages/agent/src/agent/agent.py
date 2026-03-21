"""Agent factory and async entry point."""

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP
from pydantic_ai.models import Model
from pydantic_ai.toolsets import AbstractToolset

from .deps import AgentDeps


def create_agent(
    deps: AgentDeps,
    *,
    model: Model | None = None,
    toolsets: list[AbstractToolset] | None = None,
) -> Agent[AgentDeps, str]:
    """Build a pydantic-ai Agent wired to the MCP server described in *deps*.

    The returned Agent is a plain ``pydantic_ai.Agent`` so callers can
    compose it freely — wrap it in an orchestrator, pass it as a tool, etc.

    Args:
        deps: Runtime configuration (model string, server URL, system prompt).
        model: Optional pre-built ``Model`` instance to use instead of
            ``deps.model``.  Useful for testing with ``TestModel``.
        toolsets: Override the toolset list.  Pass an empty list (``[]``) in
            unit tests to skip the live MCP server connection.

    Returns:
        A configured but not-yet-running Agent instance.
    """
    if toolsets is None:
        toolsets = [MCPServerStreamableHTTP(url=deps.server_url)]
    resolved_model: str | Model = model if model is not None else deps.model
    return Agent(
        resolved_model,
        deps_type=AgentDeps,
        toolsets=toolsets,
        system_prompt=deps.system_prompt,
    )


async def run_agent(prompt: str, deps: AgentDeps | None = None, *, model: Model | None = None) -> str:
    """Run a single prompt through the agent and return the text response.

    Args:
        prompt: The user message to send.
        deps: Optional runtime deps; defaults to ``AgentDeps()`` if omitted.
        model: Optional pre-built ``Model`` instance (e.g. ``TestModel``).

    Returns:
        The agent's text response.
    """
    deps = deps or AgentDeps()
    agent = create_agent(deps, model=model)
    async with agent.run_mcp_servers():
        result = await agent.run(prompt, deps=deps)
    return result.output
