"""Unit tests for MdReader — BM25-ranked markdown section retrieval."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_MD = str(FIXTURES_DIR / "sample.md")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def test_parse_all_sections() -> None:
    """MdReader parses the expected number of heading-delimited sections."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    reader = MdReader(SAMPLE_MD)
    assert reader.section_count >= 5


def test_file_not_found_raises() -> None:
    """Non-existent file path raises FileNotFoundError immediately."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    with pytest.raises(FileNotFoundError, match="not found"):
        MdReader("/no/such/file.md")


# ---------------------------------------------------------------------------
# Scoring & ranking
# ---------------------------------------------------------------------------


def test_exact_heading_match_ranked_first() -> None:
    """Section whose heading matches the search term exactly ranks first."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    reader = MdReader(SAMPLE_MD)
    results = reader.query("authentication")

    assert results, "Expected at least one result for 'authentication'"
    assert results[0].heading.lower() == "authentication"


def test_heading_match_outranks_content_only_match() -> None:
    """A section with the term in its heading ranks above content-only matches."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    reader = MdReader(SAMPLE_MD)
    results = reader.query("caching")

    assert results, "Expected at least one result for 'caching'"
    assert results[0].heading.lower() == "caching"


def test_multi_word_query_returns_relevant_section() -> None:
    """Multi-word search term still surfaces the most relevant section."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    reader = MdReader(SAMPLE_MD)
    results = reader.query("database indexes")

    assert results, "Expected results for 'database indexes'"
    assert results[0].heading.lower() == "database design"


def test_scored_sections_have_positive_score() -> None:
    """Every returned section has a positive BM25 score."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    reader = MdReader(SAMPLE_MD)
    results = reader.query("deployment")

    for section in results:
        assert section.score > 0, f"Section '{section.heading}' has non-positive score"


def test_results_sorted_by_score_descending() -> None:
    """Results are sorted highest score first."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    reader = MdReader(SAMPLE_MD)
    results = reader.query("monitoring observability")

    scores = [s.score for s in results]
    assert scores == sorted(scores, reverse=True), "Results must be sorted descending by score"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_no_match_returns_empty_list() -> None:
    """Unknown search term returns an empty list, not an error."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    reader = MdReader(SAMPLE_MD)
    results = reader.query("xyznonexistentterm123")

    assert results == []


def test_empty_search_term_returns_empty_list() -> None:
    """Blank or whitespace-only search term returns an empty list."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    reader = MdReader(SAMPLE_MD)
    assert reader.query("") == []
    assert reader.query("   ") == []


def test_max_sections_respected() -> None:
    """Result count never exceeds the requested max_sections."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    reader = MdReader(SAMPLE_MD)
    results = reader.query("the", max_sections=2)

    assert len(results) <= 2


def test_default_max_sections_is_three() -> None:
    """Default max_sections=3 limits output to at most 3 sections."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    reader = MdReader(SAMPLE_MD)
    # 'the' appears in most sections, so without a limit we'd get all 5
    results = reader.query("the")
    assert len(results) <= 3


def test_no_heading_file_treated_as_single_section(tmp_path: Path) -> None:
    """A markdown file with no headings is treated as a single section."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    flat = tmp_path / "flat.md"
    flat.write_text("Just some plain text without any headings.")
    reader = MdReader(str(flat))
    assert reader.section_count == 1


# ---------------------------------------------------------------------------
# list_sections
# ---------------------------------------------------------------------------


def test_list_sections_returns_all_headings() -> None:
    """list_sections includes every heading parsed from the fixture."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    reader = MdReader(SAMPLE_MD)
    sections = reader.list_sections()
    headings = [name for name, _, _level in sections]

    assert "Authentication" in headings
    assert "Database Design" in headings
    assert "Caching" in headings
    assert "Deployment" in headings
    assert "Monitoring" in headings


def test_list_sections_word_counts_are_positive() -> None:
    """Every section returned by list_sections has a positive word count."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    reader = MdReader(SAMPLE_MD)
    for heading, word_count, _level in reader.list_sections():
        assert word_count > 0, f"Section '{heading}' has zero word count"


def test_list_sections_preserves_document_order() -> None:
    """Sections are returned in the order they appear in the document."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    reader = MdReader(SAMPLE_MD)
    headings = [name for name, _, _level in reader.list_sections()]

    # fixture order: Authentication → Database Design → Caching → Deployment → Monitoring
    auth_idx = headings.index("Authentication")
    db_idx = headings.index("Database Design")
    cache_idx = headings.index("Caching")

    assert auth_idx < db_idx < cache_idx


def test_list_sections_count_matches_section_count() -> None:
    """len(list_sections()) equals section_count."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    reader = MdReader(SAMPLE_MD)
    assert len(reader.list_sections()) == reader.section_count


def test_list_sections_returns_heading_levels() -> None:
    """list_sections reports correct levels for #, ##, and ### headings."""
    from mcp_server.tool_box.md_reader.reader import MdReader

    reader = MdReader(SAMPLE_MD)
    level_map = {name: level for name, _wc, level in reader.list_sections()}

    assert level_map["Software Architecture Guide"] == 1   # #
    assert level_map["Authentication"] == 2                # ##
    assert level_map["Database Design"] == 2               # ##
    assert level_map["OAuth2"] == 3                        # ###
    assert level_map["JWT"] == 3                           # ###
