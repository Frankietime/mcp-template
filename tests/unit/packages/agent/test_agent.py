"""Unit tests for the pydantic-ai agent package.

Uses ``TestModel`` so no API key or live MCP server is required.
"""

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from agent import AgentDeps, create_agent


class TestAgentDeps:
    def test_defaults(self) -> None:
        deps = AgentDeps()
        assert deps.model == "ollama:qwen3:4b"
        assert deps.server_url == "http://127.0.0.1:8000/mcp"
        assert "/no_think" in deps.system_prompt
        assert "helpful assistant" in deps.system_prompt
        assert deps.context_window == 32_768

    def test_custom_values(self) -> None:
        deps = AgentDeps(
            model="anthropic:claude-3-5-sonnet-latest",
            server_url="http://localhost:9000/mcp",
            system_prompt="You are a specialist agent.",
        )
        assert deps.model == "anthropic:claude-3-5-sonnet-latest"
        assert deps.server_url == "http://localhost:9000/mcp"
        assert deps.system_prompt == "You are a specialist agent."


class TestCreateAgent:
    def test_returns_agent_instance(self) -> None:
        deps = AgentDeps()
        agent = create_agent(deps, model=TestModel())
        assert isinstance(agent, Agent)

    def test_custom_model_string_is_stored_in_deps(self) -> None:
        deps = AgentDeps(model="anthropic:claude-3-5-haiku-latest")
        assert deps.model == "anthropic:claude-3-5-haiku-latest"

    def test_model_kwarg_overrides_deps_model(self) -> None:
        deps = AgentDeps()
        agent = create_agent(deps, model=TestModel())
        assert isinstance(agent, Agent)

    @pytest.mark.asyncio
    async def test_run_with_test_model(self) -> None:
        deps = AgentDeps()
        test_model = TestModel(custom_output_text="test reply")
        # Pass toolsets=[] to skip the live MCP server connection in unit tests.
        agent = create_agent(deps, model=test_model, toolsets=[])
        result = await agent.run("Hello", deps=deps)
        assert isinstance(result.output, str)
        assert "test reply" in result.output
