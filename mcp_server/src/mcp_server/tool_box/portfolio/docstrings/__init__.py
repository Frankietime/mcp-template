from .portfolio_docs import (
    PORTFOLIO_GET_SECTION_V1,
    PORTFOLIO_GET_SUMMARY_V1,
    PORTFOLIO_LIST_SECTIONS_V1,
    PORTFOLIO_SEARCH_V1,
)

DOCSTRINGS: dict[str, str] = {
    "portfolio_get_summary": PORTFOLIO_GET_SUMMARY_V1,
    "portfolio_list_sections": PORTFOLIO_LIST_SECTIONS_V1,
    "portfolio_get_section": PORTFOLIO_GET_SECTION_V1,
    "portfolio_search": PORTFOLIO_SEARCH_V1,
}
