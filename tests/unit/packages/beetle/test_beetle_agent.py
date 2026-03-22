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

    def test_filter_noise_removes_http_success(self) -> None:
        logs = [
            '[ERR] mcp: Connection refused',
            '[INF] httpx: HTTP Request: POST https://api.example.com "HTTP/1.1 200 OK"',
        ]
        prompt = build_beetle_prompt(logs, "errors?", filter_noise=True)
        assert "Connection refused" in prompt
        assert "200 OK" not in prompt

    def test_filter_noise_false_leaves_all_lines(self) -> None:
        logs = [
            '[ERR] mcp: Connection refused',
            '[INF] httpx: HTTP Request: POST https://api.example.com "HTTP/1.1 200 OK"',
        ]
        prompt = build_beetle_prompt(logs, "errors?", filter_noise=False)
        assert "Connection refused" in prompt
        assert "200 OK" in prompt

    def test_active_levels_filters_by_level(self) -> None:
        logs = [
            '[DBG] httpx: connecting',
            '[ERR] mcp: Connection refused',
            '[INF] agent: Running',
        ]
        prompt = build_beetle_prompt(logs, "errors?", active_levels={"ERR"})
        assert "Connection refused" in prompt
        assert "connecting" not in prompt
        assert "Running" not in prompt

    def test_active_levels_preserves_traceback_lines(self) -> None:
        logs = [
            '[ERR] agent: Unhandled exception',
            '  File "app.py", line 10',
            '[INF] agent: Starting',
        ]
        prompt = build_beetle_prompt(logs, "what broke?", active_levels={"ERR"})
        assert "Unhandled exception" in prompt
        assert 'File "app.py"' in prompt
        assert "Starting" not in prompt

    def test_signal_fills_max_lines_after_filter(self) -> None:
        # 5 noise + 3 signal; max_lines=3 → all 3 signal lines should appear
        noise = ['[INF] httpx: HTTP Request: POST https://example.com "HTTP/1.1 200 OK"'] * 5
        signal = ['[ERR] agent: error one', '[ERR] agent: error two', '[ERR] agent: error three']
        prompt = build_beetle_prompt(noise + signal, "errors?", max_lines=3, filter_noise=True)
        assert "error one" in prompt
        assert "error two" in prompt
        assert "error three" in prompt


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
