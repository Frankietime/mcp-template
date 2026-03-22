"""Unit tests for beetle.log_filter."""

from __future__ import annotations

from beetle.log_filter import (
    NoiseRuleEntry,
    _DEFAULT_RULES,
    filter_for_context,
    is_noise,
)


class TestIsNoise:
    def test_http_200_is_noise(self) -> None:
        assert is_noise('[INF] httpx: HTTP Request: POST https://api.example.com "HTTP/1.1 200 OK"')

    def test_http_201_is_noise(self) -> None:
        assert is_noise('[INF] httpx: HTTP Request: POST https://api.example.com "HTTP/1.1 201 Created"')

    def test_http_301_is_noise(self) -> None:
        assert is_noise('[INF] httpx: HTTP Request: GET https://api.example.com "HTTP/1.1 301 Moved Permanently"')

    def test_http_404_is_not_noise(self) -> None:
        assert not is_noise('[INF] httpx: HTTP Request: POST https://api.example.com "HTTP/1.1 404 Not Found"')

    def test_http_500_is_not_noise(self) -> None:
        assert not is_noise('[INF] httpx: HTTP Request: POST https://api.example.com "HTTP/1.1 500 Internal Server Error"')

    def test_wrn_is_never_noise(self) -> None:
        assert not is_noise('[WRN] pydantic_ai: Retry limit approaching')

    def test_err_is_never_noise(self) -> None:
        assert not is_noise('[ERR] mcp.client: Connection refused')

    def test_crt_is_never_noise(self) -> None:
        assert not is_noise('[CRT] agent: Fatal error during startup')

    def test_traceback_continuation_is_signal(self) -> None:
        assert not is_noise('  File "foo.py", line 42, in send')
        assert not is_noise('    raise ConnectionError("timeout")')

    def test_debug_httpx_is_noise(self) -> None:
        assert is_noise('[DBG] httpx: h11._writer: starting')

    def test_debug_httpcore_is_noise(self) -> None:
        assert is_noise('[DBG] httpcore: send_request_headers.started')

    def test_debug_asyncio_is_noise(self) -> None:
        assert is_noise('[DBG] asyncio: Using selector: EpollSelector')

    def test_mcp_connection_error_is_signal(self) -> None:
        assert not is_noise('[ERR] mcp.client: Connection reset by peer')

    def test_mcp_lifecycle_ping_is_noise(self) -> None:
        assert is_noise('[INF] mcp: Ping')

    def test_mcp_lifecycle_server_init_is_noise(self) -> None:
        assert is_noise('[INF] mcp.server: Server initialized')

    def test_pydantic_ai_telemetry_sending_is_noise(self) -> None:
        assert is_noise('[DBG] pydantic_ai: Sending request to ollama')

    def test_pydantic_ai_telemetry_tokens_is_noise(self) -> None:
        assert is_noise('[INF] pydantic_ai: Request tokens: 1024')

    def test_disabled_rule_via_enabled_false(self) -> None:
        rules = [
            NoiseRuleEntry(r.name, r.rule, enabled=False) if r.name == "http_success" else r
            for r in _DEFAULT_RULES
        ]
        line = '[INF] httpx: HTTP Request: POST https://api.example.com "HTTP/1.1 200 OK"'
        assert not is_noise(line, rules)

    def test_custom_rule_list_replaces_defaults(self) -> None:
        # Only one rule active: anything with "BORING" in it is noise
        rules = [NoiseRuleEntry("boring", lambda line: "BORING" in line)]
        assert is_noise("[INF] agent: BORING heartbeat", rules)
        assert not is_noise('[INF] httpx: HTTP Request: POST https://example.com "HTTP/1.1 200 OK"', rules)


class TestFilterForContext:
    def test_empty_list_returns_empty(self) -> None:
        assert filter_for_context([]) == []

    def test_all_signal_unchanged(self) -> None:
        lines = [
            '[ERR] mcp.client: Connection refused',
            '[WRN] pydantic_ai: Retry limit approaching',
            '  File "foo.py", line 42',
        ]
        assert filter_for_context(lines) == lines

    def test_noise_lines_removed(self) -> None:
        lines = [
            '[ERR] mcp.client: Connection refused',
            '[INF] httpx: HTTP Request: POST https://api.example.com "HTTP/1.1 200 OK"',
            '[WRN] pydantic_ai: Retry',
        ]
        assert filter_for_context(lines) == [lines[0], lines[2]]

    def test_order_preserved(self) -> None:
        lines = [
            '[ERR] agent: First error',
            '[INF] httpx: HTTP Request: POST https://api.example.com "HTTP/1.1 200 OK"',
            '[ERR] agent: Second error',
        ]
        assert filter_for_context(lines) == [lines[0], lines[2]]

    def test_traceback_lines_preserved(self) -> None:
        lines = [
            '[ERR] agent: Unhandled exception',
            '  Traceback (most recent call last):',
            '    File "app.py", line 10, in run',
            '  ValueError: bad value',
        ]
        assert filter_for_context(lines) == lines

    def test_custom_rules_respected(self) -> None:
        custom_rule = NoiseRuleEntry("custom", lambda line: "CUSTOM_NOISE" in line)
        lines = [
            '[ERR] agent: CUSTOM_NOISE present here',
            '[WRN] agent: normal warning',
        ]
        assert filter_for_context(lines, rules=[custom_rule]) == [lines[1]]
