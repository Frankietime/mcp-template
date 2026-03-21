"""Unit tests for tui/state.py."""

from agent.tui.state import Message, TuiState


class TestMessage:
    def test_defaults(self) -> None:
        msg = Message(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"
        assert msg.complete is False

    def test_complete_flag(self) -> None:
        msg = Message(role="agent", content="hi", complete=True)
        assert msg.complete is True

    def test_all_roles(self) -> None:
        for role in ("user", "agent", "tool"):
            msg = Message(role=role, content="x")  # type: ignore[arg-type]
            assert msg.role == role


class TestTuiState:
    def test_defaults(self) -> None:
        state = TuiState()
        assert state.messages == []
        assert state.thinking is False
        assert state.mcp_connected is False
        assert state.model_name == ""
        assert state.current_agent_text == ""

    def test_append_message(self) -> None:
        state = TuiState()
        state.messages.append(Message(role="user", content="ping"))
        assert len(state.messages) == 1
        assert state.messages[0].content == "ping"

    def test_thinking_toggle(self) -> None:
        state = TuiState()
        state.thinking = True
        assert state.thinking is True
        state.thinking = False
        assert state.thinking is False

    def test_streaming_text_accumulation(self) -> None:
        state = TuiState()
        state.current_agent_text += "hel"
        state.current_agent_text += "lo"
        assert state.current_agent_text == "hello"

    def test_mcp_connected(self) -> None:
        state = TuiState()
        state.mcp_connected = True
        assert state.mcp_connected is True
