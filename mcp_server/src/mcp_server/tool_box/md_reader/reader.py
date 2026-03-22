"""Markdown section reader with BM25 ranking.

Parses any Markdown file into heading-delimited sections and ranks them
against a search term using BM25 — no embeddings, no vector database.

BM25 parameters:
    k1 = 1.5  — term frequency saturation (standard value)
    b  = 0.75 — length normalisation (standard value)

Heading boost: heading tokens are repeated _HEADING_BOOST times before
scoring so that sections whose *heading* contains the search term naturally
outrank sections that only mention it in the body.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path


_HEADING_RE = re.compile(r"^#{1,3}\s+(.+)$", re.MULTILINE)
_TOKEN_RE = re.compile(r"[a-z0-9]+")

_BM25_K1: float = 1.5
_BM25_B: float = 0.75
_HEADING_BOOST: int = 3  # heading tokens count this many times in the BM25 corpus


# ---------------------------------------------------------------------------
# Public data class
# ---------------------------------------------------------------------------


@dataclass
class ScoredSection:
    """A markdown section with its BM25 relevance score."""

    heading: str
    content: str
    score: float


# ---------------------------------------------------------------------------
# Reader
# ---------------------------------------------------------------------------


class MdReader:
    """On-demand parser and BM25 ranker for a single Markdown file.

    Does not use a singleton — instantiate per call so the tool always reads
    the current state of the file.
    """

    def __init__(self, file_path: str) -> None:
        resolved = Path(file_path).resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Markdown file not found: {resolved}")
        raw = resolved.read_text(encoding="utf-8")
        self._sections: dict[str, str] = _parse_markdown(raw)
        self.source_path = str(resolved)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def list_sections(self) -> list[tuple[str, int, int]]:
        """Return (heading, word_count, level) for every parsed section in document order."""
        return [
            (name, len(content.split()), level)
            for name, (content, level) in self._sections.items()
        ]

    def query(self, search_term: str, max_sections: int = 3) -> list[ScoredSection]:
        """Return the top *max_sections* sections most relevant to *search_term*.

        Uses BM25 over tokenised section text (heading words are weighted via
        repetition so heading matches naturally outrank body-only matches).

        Returns an empty list when *search_term* is blank or no section matches.
        """
        if not search_term.strip():
            return []

        query_terms = _tokenize(search_term)
        if not query_terms:
            return []

        # Build corpus: each entry is (heading, content, tokens)
        # Heading tokens are repeated _HEADING_BOOST times for implicit boosting.
        corpus: list[tuple[str, str, list[str]]] = [
            (heading, content, _tokenize(heading) * _HEADING_BOOST + _tokenize(content))
            for heading, (content, _level) in self._sections.items()
        ]

        raw_scores = _bm25_scores(query_terms, [tokens for _, _, tokens in corpus])

        results = [
            ScoredSection(heading=heading, content=content, score=score)
            for (heading, content, _), score in zip(corpus, raw_scores)
            if score > 0
        ]
        results.sort(key=lambda s: s.score, reverse=True)
        return results[:max_sections]

    @property
    def section_count(self) -> int:
        """Number of parsed sections (including preamble if non-empty)."""
        return len(self._sections)


# ---------------------------------------------------------------------------
# BM25 implementation (pure Python, no external dependencies)
# ---------------------------------------------------------------------------


def _bm25_scores(query_terms: list[str], corpus: list[list[str]]) -> list[float]:
    """Return a BM25 score for each document in *corpus* given *query_terms*."""
    n_docs = len(corpus)
    if n_docs == 0:
        return []

    avg_len = sum(len(doc) for doc in corpus) / n_docs

    # Document frequency: number of docs containing each term
    df: dict[str, int] = {}
    for doc in corpus:
        for term in set(doc):
            df[term] = df.get(term, 0) + 1

    scores: list[float] = []
    for doc in corpus:
        doc_len = len(doc)
        tf_map: dict[str, int] = {}
        for token in doc:
            tf_map[token] = tf_map.get(token, 0) + 1

        score = 0.0
        for term in query_terms:
            n_t = df.get(term, 0)
            if n_t == 0:
                continue
            freq = tf_map.get(term, 0)
            # Robertson smoothed IDF
            idf = math.log((n_docs - n_t + 0.5) / (n_t + 0.5) + 1)
            # BM25 TF component with length normalisation
            tf = freq * (_BM25_K1 + 1) / (
                freq + _BM25_K1 * (1 - _BM25_B + _BM25_B * doc_len / avg_len)
            )
            score += idf * tf

        scores.append(score)

    return scores


# ---------------------------------------------------------------------------
# Markdown parsing
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> list[str]:
    """Lowercase and split *text* into alphanumeric tokens."""
    return _TOKEN_RE.findall(text.lower())


def _parse_markdown(text: str) -> dict[str, tuple[str, int]]:
    """Split Markdown text into sections keyed by heading text.

    Sections are delimited by H1 (#), H2 (##), or H3 (###) headings.
    Content before the first heading is stored under '__preamble__'.
    Files without any headings are stored as a single 'Document' section.
    Duplicate headings get a numeric suffix to preserve order.

    Values are ``(content, level)`` tuples where *level* is 1 for ``#``,
    2 for ``##``, 3 for ``###`` (preamble and Document sections use level 0).
    """
    sections: dict[str, tuple[str, int]] = {}
    matches = list(_HEADING_RE.finditer(text))

    if not matches:
        sections["Document"] = (text.strip(), 0)
        return sections

    preamble = text[: matches[0].start()].strip()
    if preamble:
        sections["__preamble__"] = (preamble, 0)

    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        level = len(match.group(0)) - len(match.group(0).lstrip("#"))
        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()

        key = heading
        counter = 2
        while key in sections:
            key = f"{heading} ({counter})"
            counter += 1
        sections[key] = (body, level)

    return sections
