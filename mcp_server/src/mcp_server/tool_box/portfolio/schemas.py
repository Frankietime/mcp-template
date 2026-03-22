from pydantic import BaseModel


class SectionItem(BaseModel):
    """A single section name from the portfolio."""

    name: str
    word_count: int


class SectionContent(BaseModel):
    """Full content of a portfolio section."""

    name: str
    content: str
    word_count: int


class SearchMatch(BaseModel):
    """A keyword match inside the portfolio."""

    section: str
    excerpt: str


class SearchResult(BaseModel):
    """Results from a portfolio keyword search."""

    query: str
    total_matches: int
    matches: list[SearchMatch]
