"""Unit tests for ContextBarControl."""

from __future__ import annotations

from agent.tui.components.context_bar import ContextBarControl, _BAR_WIDTH, _EMPTY, _FILL
from agent.tui.state import TuiState


def _fragments(used: int, max_: int) -> list:
    state = TuiState(context_tokens_used=used, context_tokens_max=max_)
    bar = ContextBarControl(state)
    return bar._get_fragments()


class TestContextBarFragments:
    def test_empty_state_shows_full_empty_bar(self) -> None:
        frags = _fragments(0, 32_768)
        bar_text = next(text for _, text in frags if _EMPTY in text or _FILL in text)
        assert bar_text == _EMPTY * _BAR_WIDTH

    def test_full_state_shows_full_fill_bar(self) -> None:
        frags = _fragments(32_768, 32_768)
        bar_text = next(text for _, text in frags if _FILL in text or _EMPTY in text)
        assert bar_text == _FILL * _BAR_WIDTH

    def test_half_filled_bar(self) -> None:
        frags = _fragments(16_384, 32_768)
        bar_text = next(text for _, text in frags if _FILL in text or _EMPTY in text)
        half = _BAR_WIDTH // 2
        assert bar_text.count(_FILL) == half
        assert bar_text.count(_EMPTY) == half

    def test_label_shows_token_counts(self) -> None:
        frags = _fragments(1_000, 32_768)
        label = next(text for _, text in frags if "/" in text)
        assert "1,000" in label
        assert "32,768" in label

    def test_label_shows_percentage(self) -> None:
        frags = _fragments(16_384, 32_768)
        label = next(text for _, text in frags if "%" in text)
        assert "50%" in label

    def test_zero_max_does_not_divide_by_zero(self) -> None:
        frags = _fragments(0, 0)
        assert frags  # just verify it renders without error


class TestContextBarStyle:
    def test_below_70_percent_is_green(self) -> None:
        frags = _fragments(10_000, 32_768)  # ~30%
        bar_style = next(style for style, text in frags if _FILL in text or _EMPTY in text)
        assert bar_style == "ansigreen"

    def test_above_70_percent_is_yellow(self) -> None:
        frags = _fragments(25_000, 32_768)  # ~76%
        bar_style = next(style for style, text in frags if _FILL in text or _EMPTY in text)
        assert bar_style == "ansiyellow"

    def test_above_90_percent_is_bold_red(self) -> None:
        frags = _fragments(31_000, 32_768)  # ~95%
        bar_style = next(style for style, text in frags if _FILL in text or _EMPTY in text)
        assert bar_style == "bold ansired"
