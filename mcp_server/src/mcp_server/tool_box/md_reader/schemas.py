from pydantic import BaseModel


class SectionIndex(BaseModel):
    """A single row returned by md_list_sections."""

    heading: str
    level: int
    word_count: int


class MatchedSection(BaseModel):
    """A single markdown section returned by md_query."""

    heading: str
    content: str
    word_count: int
    score: float


class QueryResult(BaseModel):
    """Full result returned by md_query."""

    file_path: str
    search_term: str
    total_sections: int
    sections: list[MatchedSection]
