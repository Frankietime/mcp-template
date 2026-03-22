"""Unit tests for tui/components/ and tui/key_bindings.py."""

from __future__ import annotations

from unittest.mock import MagicMock

from equator.components.history import HistoryControl
from equator.components.status import StatusControl, _MCP_OK, _MCP_WAIT
from equator.key_bindings import build_key_bindings
from equator.state import TuiState


# ---------------------------------------------------------------------------
# HistoryControl
# ---------------------------------------------------------------------------


class TestHistoryControl:
    def _ctrl(self, state: TuiState | None = None) -> HistoryControl:
        return HistoryControl(state or TuiState())

    def _text(self, ctrl: HistoryControl) -> str:
        return "".join(text for _, text in ctrl._get_fragments())

    def test_empty_control_is_empty(self) -> None:
        assert self._text(self._ctrl()) == ""

    def test_user_message_rendered(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_user_message("ping")
        assert "ping" in self._text(ctrl)

    def test_agent_message_rendered(self) -> None:
        ctrl = self._ctrl()
        ctrl.start_agent_stream()
        ctrl.append_delta("pong")
        ctrl.end_agent_stream("pong")
        assert "pong" in self._text(ctrl)

    def test_agent_message_uses_agent_style(self) -> None:
        ctrl = self._ctrl()
        ctrl.start_agent_stream(agent_id="beetle")
        ctrl.end_agent_stream("hello")
        styles = [style for style, _ in ctrl._get_fragments()]
        assert any("msg.agent" in s for s in styles)

    def test_tool_message_rendered(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_tool_call("search")
        assert "search" in self._text(ctrl)

    def test_thinking_shows_loader_frame(self) -> None:
        state = TuiState(thinking=True, loader_frame=0)
        ctrl = HistoryControl(state)
        text = self._text(ctrl)
        assert text.strip() != ""  # some spinner content is rendered

    def test_thinking_with_streaming_shows_cursor(self) -> None:
        state = TuiState(thinking=True)
        ctrl = HistoryControl(state)
        ctrl.start_agent_stream()
        ctrl.append_delta("hel")
        text = self._text(ctrl)
        assert "hel" in text
        assert "\u258b" in text  # cursor glyph

    def test_clear_removes_messages(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_user_message("hi")
        ctrl.clear()
        assert self._text(ctrl) == ""

    def test_complete_last_tool_marks_complete(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_tool_call("search")
        assert ctrl._messages[0].complete is False
        ctrl.complete_last_tool()
        assert ctrl._messages[0].complete is True

    def test_end_agent_stream_with_no_delta_uses_final_output(self) -> None:
        ctrl = self._ctrl()
        ctrl.start_agent_stream()
        ctrl.end_agent_stream("direct output")
        assert "direct output" in self._text(ctrl)


# ---------------------------------------------------------------------------
# StatusControl
# ---------------------------------------------------------------------------


class TestStatusControl:
    def _text(self, state: TuiState) -> str:
        ctrl = StatusControl(state)
        return "".join(text for _, text in ctrl._get_fragments())

    def test_model_name_shown(self) -> None:
        state = TuiState(model_name="ollama:phi4-mini:3.8b")
        assert "ollama:phi4-mini:3.8b" in self._text(state)

    def test_mcp_connected_symbol(self) -> None:
        state = TuiState(mcp_connected=True)
        assert _MCP_OK in self._text(state)

    def test_mcp_disconnected_symbol(self) -> None:
        state = TuiState(mcp_connected=False)
        assert _MCP_WAIT in self._text(state)

    def test_thinking_indicator_shown(self) -> None:
        state = TuiState(thinking=True)
        assert "Thinking" in self._text(state)

    def test_thinking_indicator_hidden_when_not_thinking(self) -> None:
        state = TuiState(thinking=False)
        assert "Thinking" not in self._text(state)

    def test_spinner_advances(self) -> None:
        state = TuiState(thinking=True)
        ctrl = StatusControl(state)
        frame_before = ctrl._spinner_index
        ctrl.tick()
        assert ctrl._spinner_index == (frame_before + 1) % 10


# ---------------------------------------------------------------------------
# KeyBindings
# ---------------------------------------------------------------------------


class TestKeyBindings:
    def _kb(self):
        _noop = MagicMock()
        _false = lambda: False  # noqa: E731
        _true = lambda: True   # noqa: E731
        return build_key_bindings(
            on_quit=_noop,
            on_clear=_noop,
            on_show_logs=_noop,
            on_show_main=_noop,
            on_model_up=_noop,
            on_model_down=_noop,
            on_model_confirm=_noop,
            on_model_cancel=_noop,
            on_cursor_prev=_noop,
            on_cursor_next=_noop,
            on_log_page_back=_noop,
            on_log_page_forward=_noop,
            on_detail_toggle=_noop,
            on_detail_exit=_noop,
            on_detail_tool_prev=_noop,
            on_detail_tool_next=_noop,
            on_toggle_help=_noop,
            model_selector_open=_false,
            logs_panel_active=_false,
            detail_mode_active=_false,
            input_is_empty=_true,
            cursor_active=_false,
        )

    def test_quit_callback_registered(self) -> None:
        keys = [str(b.keys) for b in self._kb().bindings]
        assert any("c-x" in k for k in keys)

    def test_f2_detail_toggle_registered(self) -> None:
        keys = [str(b.keys) for b in self._kb().bindings]
        assert any("f2" in k for k in keys)

    def test_tab_toggles_help_binding_registered(self) -> None:
        keys = [str(b.keys) for b in self._kb().bindings]
        assert any("tab" in k for k in keys)


# ---------------------------------------------------------------------------
# Inspect / detail feature — tool call visibility and navigation
# ---------------------------------------------------------------------------


class TestHistoryInspect:
    """Tests for message cursor navigation and inline detail rendering."""

    def _ctrl(self, state: TuiState | None = None) -> HistoryControl:
        return HistoryControl(state or TuiState())

    def _text(self, ctrl: HistoryControl) -> str:
        return "".join(text for _, text in ctrl._get_fragments())

    def _styles(self, ctrl: HistoryControl) -> list[str]:
        return [style for style, _ in ctrl._get_fragments()]

    # -- storage -----------------------------------------------------------

    def test_tool_call_args_stored(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_tool_call("md_query", {"query": "Python"})
        assert ctrl._messages[0].tool_args == {"query": "Python"}

    def test_tool_call_result_stored_after_complete(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_tool_call("md_query", {"query": "Python"})
        ctrl.complete_last_tool("Found 2 matches")
        assert ctrl._messages[0].tool_result == "Found 2 matches"
        assert ctrl._messages[0].complete is True

    def test_multiple_tool_calls_stored_independently(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_tool_call("md_list_sections", {})
        ctrl.add_tool_call("md_list_sections", {"section_name": "Skills"})
        ctrl.complete_last_tool("Skills content")
        # first tool still incomplete
        assert ctrl._messages[0].complete is False
        assert ctrl._messages[1].complete is True
        assert ctrl._messages[1].tool_result == "Skills content"

    def test_tool_messages_use_tool_style(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_tool_call("md_query")
        styles = self._styles(ctrl)
        assert any("msg.tool" in s for s in styles)

    def test_completed_tool_uses_done_style(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_tool_call("md_query")
        ctrl.complete_last_tool("result")
        styles = self._styles(ctrl)
        assert any("msg.tool.done" in s for s in styles)

    # -- message cursor ----------------------------------------------------

    def test_cursor_prev_activates_cursor(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_user_message("hello")
        assert ctrl.cursor_active is False
        ctrl.cursor_prev()
        assert ctrl.cursor_active is True

    def test_cursor_next_at_last_message_returns_to_auto_follow(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_user_message("hello")
        ctrl.cursor_prev()   # select last message
        ctrl.cursor_next()   # step forward → back to auto-follow
        assert ctrl.cursor_active is False

    def test_follow_latest_clears_cursor(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_user_message("hello")
        ctrl.cursor_prev()
        ctrl.follow_latest()
        assert ctrl.cursor_active is False

    def test_cursor_prev_on_empty_history_is_noop(self) -> None:
        ctrl = self._ctrl()
        ctrl.cursor_prev()
        assert ctrl.cursor_active is False

    # -- inline detail (compact) -------------------------------------------

    def test_inline_detail_shown_when_cursor_active(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_user_message("hello")
        ctrl.add_tool_call("md_query", {"query": "Python"})
        ctrl.complete_last_tool("result")
        ctrl.cursor_prev()  # activate cursor on tool message
        text = self._text(ctrl)
        assert "detail" in " ".join(self._styles(ctrl))  # detail styles present

    def test_inline_detail_compact_shows_tool_name(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_tool_call("md_query", {"query": "Python"})
        ctrl.complete_last_tool("2 matches")
        ctrl.cursor_prev()  # compact mode (detail_mode=False)
        text = self._text(ctrl)
        assert "md_query" in text

    def test_inline_detail_compact_shows_complete_checkmark(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_tool_call("md_query")
        ctrl.complete_last_tool("done")
        ctrl.cursor_prev()
        text = self._text(ctrl)
        assert "\u2713" in text  # ✓

    # -- inline detail (expanded, F2 mode) ---------------------------------

    def test_inline_detail_expanded_shows_args(self) -> None:
        state = TuiState()
        ctrl = HistoryControl(state)
        ctrl.add_tool_call("md_query", {"query": "Python"})
        ctrl.complete_last_tool("2 matches")
        ctrl.enter_detail()  # F2 equivalent
        text = self._text(ctrl)
        assert "Python" in text

    def test_inline_detail_expanded_shows_result(self) -> None:
        state = TuiState()
        ctrl = HistoryControl(state)
        ctrl.add_tool_call("md_query", {"query": "Python"})
        ctrl.complete_last_tool("2 matches found")
        ctrl.enter_detail()
        text = self._text(ctrl)
        assert "2 matches found" in text

    def test_inline_detail_expanded_pending_tool_shows_pending(self) -> None:
        state = TuiState()
        ctrl = HistoryControl(state)
        ctrl.add_tool_call("md_query", {"query": "Python"})
        # do NOT complete — still pending
        ctrl.enter_detail()
        text = self._text(ctrl)
        assert "pending" in text

    # -- tool cycling (Left/Right) -----------------------------------------

    def test_detail_tool_next_cycles_through_tools(self) -> None:
        state = TuiState()
        ctrl = HistoryControl(state)
        ctrl.add_user_message("list and search")
        ctrl.add_tool_call("md_list_sections", {})
        ctrl.complete_last_tool("sections")
        ctrl.add_tool_call("md_query", {"query": "Python"})
        ctrl.complete_last_tool("matches")
        ctrl.add_tool_call("md_list_sections", {"section_name": "Skills"})
        ctrl.complete_last_tool("skills content")
        ctrl.start_agent_stream()
        ctrl.end_agent_stream("done")

        ctrl.cursor_prev()   # select agent message (last)
        ctrl.enter_detail()
        # cycle to first tool
        ctrl.detail_tool_next()
        tool = ctrl.selected_tool()
        assert tool is not None
        assert "md_list_sections" in tool.content

    def test_detail_tool_prev_wraps_around(self) -> None:
        state = TuiState()
        ctrl = HistoryControl(state)
        ctrl.add_user_message("q")
        ctrl.add_tool_call("md_list_sections", {})
        ctrl.complete_last_tool("s")
        ctrl.add_tool_call("md_query", {"query": "x"})
        ctrl.complete_last_tool("r")
        ctrl.start_agent_stream()
        ctrl.end_agent_stream("done")

        ctrl.cursor_prev()
        ctrl.enter_detail()
        ctrl.detail_tool_prev()   # wraps to last tool
        tool = ctrl.selected_tool()
        assert tool is not None
        assert "md_query" in tool.content

    def test_all_tools_in_turn_visible_when_cycling(self) -> None:
        state = TuiState()
        ctrl = HistoryControl(state)
        ctrl.add_user_message("q")
        tool_names = [
            "md_query",
            "md_list_sections",
            "md_list_sections",
        ]
        for name in tool_names:
            ctrl.add_tool_call(name, {})
            ctrl.complete_last_tool("ok")
        ctrl.start_agent_stream()
        ctrl.end_agent_stream("done")

        ctrl.cursor_prev()
        ctrl.enter_detail()

        seen: list[str] = []
        for _ in range(len(tool_names)):
            ctrl.detail_tool_next()
            tool = ctrl.selected_tool()
            assert tool is not None
            seen.append(tool.content)

        for name in tool_names:
            assert any(name in s for s in seen), f"{name} not seen when cycling tools"

    # -- turn grouping -----------------------------------------------------

    def test_build_turns_groups_tools_with_user_and_agent(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_user_message("q")
        ctrl.add_tool_call("md_query", {})
        ctrl.complete_last_tool("r")
        ctrl.start_agent_stream()
        ctrl.end_agent_stream("done")
        turns = ctrl._build_turns()
        assert len(turns) == 1
        assert turns[0].user_idx == 0
        assert len(turns[0].tool_idxs) == 1
        assert turns[0].agent_idx == 2

    def test_selected_turn_tools_returns_tools_for_selected_message(self) -> None:
        ctrl = self._ctrl()
        ctrl.add_user_message("q")
        ctrl.add_tool_call("md_query", {})
        ctrl.complete_last_tool("r")
        ctrl.start_agent_stream()
        ctrl.end_agent_stream("done")
        ctrl.cursor_prev()   # select agent message
        tools = ctrl._selected_turn_tools()
        assert len(tools) == 1
        assert "md_query" in tools[0].content
