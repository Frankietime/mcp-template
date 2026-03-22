"""Unit tests for tui/commands.py."""

from __future__ import annotations

from unittest.mock import MagicMock

from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document

from tui.commands import CommandKind, CommandRegistry, PREFIX, SlashCompleter
from tui.state import TuiState


def _app() -> MagicMock:
    app = MagicMock()
    app.invalidate = MagicMock()
    return app


def _registry() -> CommandRegistry:
    from tui.commands import registry
    return registry


class TestIsCommand:
    def test_plain_text_is_not_command(self) -> None:
        assert _registry().is_command("hello world") is False

    def test_slash_mid_sentence_is_not_command(self) -> None:
        assert _registry().is_command("yes/ I agree") is False

    def test_slash_digit_is_command(self) -> None:
        assert _registry().is_command("/1") is True

    def test_slash_word_is_command(self) -> None:
        assert _registry().is_command("/print") is True

    def test_slash_mixed_alphanumeric_is_command(self) -> None:
        assert _registry().is_command("/log2") is True

    def test_prefix_is_slash(self) -> None:
        assert PREFIX == "/"


class TestHandle:
    def test_non_command_returns_false(self) -> None:
        assert _registry().handle("hello", TuiState(), _app()) is False

    def test_known_command_returns_true(self) -> None:
        assert _registry().handle("/help", TuiState(), _app()) is True

    def test_unknown_command_returns_true_and_warns(self) -> None:
        state = TuiState()
        _registry().handle("/9", state, _app())
        assert any("9" in line for line in state.log_lines)
        assert state.active_panel == "logs"


class TestCommandKind:
    def test_three_kinds_exist(self) -> None:
        assert CommandKind.ACTION
        assert CommandKind.PROMPT
        assert CommandKind.SCRIPT

    def test_default_kind_is_action(self) -> None:
        reg = CommandRegistry()
        reg.register("x", "test")(lambda *_: None)
        assert reg.get("x") is not None
        assert reg.get("x").kind == CommandKind.ACTION  # type: ignore[union-attr]


class TestCommandRegistryGet:
    def test_get_known_returns_command(self) -> None:
        reg = CommandRegistry()
        reg.register("hi", "says hi")(lambda *_: None)
        cmd = reg.get("hi")
        assert cmd is not None
        assert cmd.name == "hi"

    def test_get_unknown_returns_none(self) -> None:
        reg = CommandRegistry()
        assert reg.get("missing") is None


class TestRegisterWithKind:
    def test_prompt_kind_and_template_stored(self) -> None:
        reg = CommandRegistry()
        reg.register("fill", "fill template", kind=CommandKind.PROMPT, template="Do this: ")(
            lambda *_: None
        )
        cmd = reg.get("fill")
        assert cmd is not None
        assert cmd.kind == CommandKind.PROMPT
        assert cmd.template == "Do this: "

    def test_script_kind_and_template_stored(self) -> None:
        reg = CommandRegistry()
        reg.register("run", "run now", kind=CommandKind.SCRIPT, template="Execute plan")(
            lambda *_: None
        )
        cmd = reg.get("run")
        assert cmd is not None
        assert cmd.kind == CommandKind.SCRIPT
        assert cmd.template == "Execute plan"


class TestSlashCompleter:
    def _make_completer(self) -> SlashCompleter:
        reg = CommandRegistry()
        reg.register("help", "show help")(lambda *_: None)
        reg.register("quit", "quit app")(lambda *_: None)
        reg.register("history", "show history")(lambda *_: None)
        return SlashCompleter(reg)

    def _complete(self, completer: SlashCompleter, text: str) -> list:
        doc = Document(text=text, cursor_position=len(text))
        event = CompleteEvent(completion_requested=False)
        return list(completer.get_completions(doc, event))

    def test_no_completions_for_plain_text(self) -> None:
        c = self._make_completer()
        assert self._complete(c, "hello") == []

    def test_no_completions_for_empty_string(self) -> None:
        c = self._make_completer()
        assert self._complete(c, "") == []

    def test_slash_alone_returns_all_commands(self) -> None:
        c = self._make_completer()
        results = self._complete(c, "/")
        assert len(results) == 3

    def test_partial_filters_correctly(self) -> None:
        c = self._make_completer()
        results = self._complete(c, "/h")
        names = [r.text for r in results]
        assert "help" in names
        assert "history" in names
        assert "quit" not in names

    def test_full_match_returns_single_result(self) -> None:
        c = self._make_completer()
        results = self._complete(c, "/quit")
        assert len(results) == 1
        assert results[0].text == "quit"

    def test_no_completions_when_space_after_partial(self) -> None:
        c = self._make_completer()
        assert self._complete(c, "/help me") == []

    def _display_text(self, value: object) -> str:
        """Extract plain text from a Completion display/display_meta field."""
        from prompt_toolkit.formatted_text import to_formatted_text
        return "".join(text for _, text in to_formatted_text(value))

    def test_display_has_slash_prefix(self) -> None:
        c = self._make_completer()
        results = self._complete(c, "/q")
        assert len(results) == 1
        assert self._display_text(results[0].display) == "/quit"

    def test_display_meta_is_description(self) -> None:
        c = self._make_completer()
        results = self._complete(c, "/quit")
        assert self._display_text(results[0].display_meta) == "quit app"

    def test_start_position_replaces_partial(self) -> None:
        c = self._make_completer()
        results = self._complete(c, "/qu")
        assert results[0].start_position == -2

    def test_start_position_zero_for_full_slash(self) -> None:
        c = self._make_completer()
        results = self._complete(c, "/")
        for r in results:
            assert r.start_position == 0


class TestBuiltinCommands:
    def test_help_populates_log_lines_and_opens_logs(self) -> None:
        state = TuiState()
        _registry().handle("/help", state, _app())
        assert any("/" in line for line in state.log_lines)
        assert state.active_panel == "logs"

    def test_help_does_not_show_interpret_in_base_registry(self) -> None:
        """interpret is agent-specific — absent from the shared base registry."""
        state = TuiState()
        _registry().handle("/help", state, _app())
        assert not any("interpret" in line for line in state.log_lines)


class TestRegistryExtend:
    def test_child_inherits_parent_commands(self) -> None:
        parent = CommandRegistry()
        parent.register("foo", "foo cmd")(lambda *_: None)
        child = parent.extend()
        assert child.get("foo") is not None

    def test_child_additions_do_not_affect_parent(self) -> None:
        parent = CommandRegistry()
        child = parent.extend()
        child.register("bar", "bar cmd")(lambda *_: None)
        assert parent.get("bar") is None

    def test_parent_additions_do_not_affect_child(self) -> None:
        parent = CommandRegistry()
        child = parent.extend()
        parent.register("baz", "baz cmd")(lambda *_: None)
        assert child.get("baz") is None

    def test_lab_mouse_registry_has_interpret(self) -> None:
        from lab_mouse.tui.commands import registry as lab_registry
        assert lab_registry.get("interpret") is not None

    def test_base_registry_does_not_have_interpret(self) -> None:
        from tui.commands import registry as base_registry
        assert base_registry.get("interpret") is None
