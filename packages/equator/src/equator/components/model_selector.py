"""Floating model selector control."""

from __future__ import annotations

from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.layout.controls import FormattedTextControl

from ..state import TuiState


class ModelSelectorControl(FormattedTextControl):
    """Renders a navigable list of available models.

    Reads ``state.available_models`` and ``state.model_selector_idx``.
    Shows a "fetching…" placeholder until the list is populated.
    """

    def __init__(self, state: TuiState) -> None:
        super().__init__(lambda: self._get_fragments(), focusable=False)
        self._state = state

    def _get_fragments(self) -> StyleAndTextTuples:
        if not self._state.available_models:
            return [("class:selector.empty", "  fetching models…\n")]
        frags: StyleAndTextTuples = []
        for i, model in enumerate(self._state.available_models):
            if i == self._state.model_selector_idx:
                frags.append(("class:selector.selected", f" ▸ {model}\n"))
            else:
                frags.append(("class:selector.item", f"   {model}\n"))
        return frags
