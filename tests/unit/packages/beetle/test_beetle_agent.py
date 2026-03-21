"""Unit tests for the beetle agent package."""

from __future__ import annotations

from unittest.mock import patch

from beetle import BEETLE_SYMBOL, build_beetle_prompt, create_beetle_agent


class TestBeetleSymbol:
    def test_symbol_value(self) -> None:
        assert BEETLE_SYMBOL == "=){"


class TestBuildBeetlePrompt:
    def test_empty_logs(self) -> None:
        prompt = build_beetle_prompt([], "is anything failing?")
        assert "empty" in prompt
        assert "is anything failing?" in prompt

    def test_log_lines_included(self) -> None:
        logs = ["INFO connecting", "ERROR timeout"]
        prompt = build_beetle_prompt(logs, "why did it fail?")
        assert "INFO connecting" in prompt
        assert "ERROR timeout" in prompt
        assert "why did it fail?" in prompt

    def test_caps_at_200_lines(self) -> None:
        logs = [f"line {i}" for i in range(300)]
        prompt = build_beetle_prompt(logs, "anything?")
        assert "line 299" in prompt
        assert "line 0" not in prompt


class TestCreateBeetleAgent:
    def test_returns_agent_with_no_tools(self) -> None:
        with patch("beetle.agent.Agent") as MockAgent:
            create_beetle_agent()
            _, kwargs = MockAgent.call_args
            assert kwargs.get("toolsets") == []

    def test_uses_beetle_model_env_var(self) -> None:
        with patch("beetle.agent.Agent") as MockAgent, \
             patch("beetle.agent.os.getenv", return_value="ollama:custom:1b"):
            create_beetle_agent()
            args, _ = MockAgent.call_args
            assert args[0] == "ollama:custom:1b"
