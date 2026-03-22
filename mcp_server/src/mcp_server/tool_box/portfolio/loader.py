"""Portfolio Markdown loader.

Parses a single Markdown file into named sections keyed by heading text.
Sections are delimited by H1 (#) or H2 (##) headings; everything before the
first heading is stored under the special key "__preamble__".

Exposes a module-level singleton so tools can access the loaded data without
passing it around at runtime.
"""

from __future__ import annotations

import re
from pathlib import Path


_HEADING_RE = re.compile(r"^#{1,2}\s+(.+)$", re.MULTILINE)

_EXCERPT_WINDOW = 120  # characters on each side of a keyword match


class PortfolioLoader:
    """Parsed in-memory representation of a Markdown portfolio file."""

    def __init__(self, sections: dict[str, str], source_path: str) -> None:
        self._sections = sections  # ordered dict: heading → body text
        self.source_path = source_path

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_summary(self) -> tuple[str, str]:
        """Return (name, content) of the first meaningful section."""
        for name, content in self._sections.items():
            if content.strip():
                return name, content
        return ("", "")

    def list_sections(self) -> list[tuple[str, int]]:
        """Return list of (section_name, word_count) for every section."""
        return [
            (name, len(content.split()))
            for name, content in self._sections.items()
            if name != "__preamble__" or content.strip()
        ]

    def get_section(self, name: str) -> tuple[str, str] | None:
        """Return (name, content) for a case-insensitive section name match.

        Returns None if no section matches.
        """
        needle = name.strip().lower()
        for key, content in self._sections.items():
            if key.lower() == needle:
                return key, content
        # fuzzy: section name starts with the query
        for key, content in self._sections.items():
            if key.lower().startswith(needle):
                return key, content
        return None

    def search(self, query: str) -> list[tuple[str, str]]:
        """Case-insensitive keyword search across all sections.

        Returns list of (section_name, excerpt) where each excerpt is a
        ~240-character window centred on the match.
        """
        needle = query.strip().lower()
        matches: list[tuple[str, str]] = []
        for section_name, content in self._sections.items():
            lower_content = content.lower()
            start = 0
            while True:
                idx = lower_content.find(needle, start)
                if idx == -1:
                    break
                lo = max(0, idx - _EXCERPT_WINDOW)
                hi = min(len(content), idx + len(needle) + _EXCERPT_WINDOW)
                excerpt = ("…" if lo > 0 else "") + content[lo:hi].strip() + ("…" if hi < len(content) else "")
                matches.append((section_name, excerpt))
                start = idx + len(needle)
        return matches

    @property
    def section_count(self) -> int:
        return len([n for n, c in self.list_sections()])


# ------------------------------------------------------------------
# Module-level singleton
# ------------------------------------------------------------------

_portfolio: PortfolioLoader | None = None


def load_portfolio(path: str) -> PortfolioLoader:
    """Parse the Markdown file at *path* and cache it as the singleton.

    Call once during server startup (app_lifespan).
    """
    global _portfolio
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(
            f"Portfolio file not found: {resolved}\n"
            "Create it or set PORTFOLIO_MD_PATH to a valid path."
        )

    raw = resolved.read_text(encoding="utf-8")
    sections = _parse_markdown(raw)
    _portfolio = PortfolioLoader(sections, str(resolved))
    return _portfolio


def get_portfolio() -> PortfolioLoader:
    """Return the loaded portfolio singleton.

    Raises RuntimeError if load_portfolio() has not been called yet.
    """
    if _portfolio is None:
        raise RuntimeError(
            "Portfolio not loaded. Ensure load_portfolio() is called during app_lifespan."
        )
    return _portfolio


# ------------------------------------------------------------------
# Markdown parsing
# ------------------------------------------------------------------

def _parse_markdown(text: str) -> dict[str, str]:
    """Split Markdown text into sections keyed by heading text.

    Everything before the first heading lands in '__preamble__'.
    """
    sections: dict[str, str] = {}
    matches = list(_HEADING_RE.finditer(text))

    if not matches:
        # No headings — entire file is the summary
        sections["Profile"] = text.strip()
        return sections

    # Preamble (before first heading)
    preamble = text[: matches[0].start()].strip()
    if preamble:
        sections["__preamble__"] = preamble

    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        # If duplicate headings exist, append a counter suffix
        key = heading
        counter = 2
        while key in sections:
            key = f"{heading} ({counter})"
            counter += 1
        sections[key] = body

    return sections
