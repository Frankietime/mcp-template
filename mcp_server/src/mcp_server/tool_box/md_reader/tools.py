from pathlib import Path
from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from mcp_shared import ErrorResponse, NextStep, ResponseFormat, SummaryResponse
from mcp_shared.logging import track_tool_execution
from mcp_shared.token_usage import log_token_usage
from pydantic import Field

from .docstrings import DOCSTRINGS
from .reader import MdReader
from .schemas import MatchedSection, QueryResult, SectionIndex
from .tool_names import ToolNames

# ---------------------------------------------------------------------------
# File registry
# Paths are resolved relative to this file so the server works from any cwd.
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).parents[4] / "data"

MdFileKey = Literal["RESUME", "RESUME_CREATIVE", "RESUME_EXTENDED"]

_FILE_MAP: dict[str, Path] = {
    "RESUME": _DATA_DIR / "RESUME.md",
    "RESUME_CREATIVE": _DATA_DIR / "RESUME_CREATIVE.md",
    "RESUME_EXTENDED": _DATA_DIR / "RESUME_EXTENDED.md",
}

_FILE_ANNOTATION = (
    "Which document to query. Available files:\n"
    "  • RESUME          — Standard professional resume. Senior Full Stack / AI Engineer framing. "
    "Work history, skills, and tech summary. Best for role-fit and technical background questions.\n"
    "  • RESUME_CREATIVE — Narrative-first version. Technical Creative Producer framing. "
    "Emphasises the music / film / sound-design background alongside engineering. "
    "Best for creative-tech roles or culture-fit questions.\n"
    "  • RESUME_EXTENDED — Full extended resume. Includes a 'Unique Value Proposition' section "
    "and deeper project detail. Best for comprehensive background or research-oriented questions."
)


def add_tool(mcp: FastMCP) -> None:
    """Register md_list_sections and md_query tools with the MCP server."""

    @mcp.tool(
        name=ToolNames.MD_LIST_SECTIONS,
        description=DOCSTRINGS["md_list_sections"],
        annotations={
            "title": "List Markdown Sections",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        tags={"documents", "discovery"},
        output_schema={
            "type": "object",
            "properties": {
                "sections": {
                    "type": "array",
                    "items": SectionIndex.model_json_schema(),
                }
            },
            "required": ["sections"],
        },
    )
    @track_tool_execution
    async def md_list_sections(
        document: Annotated[MdFileKey, _FILE_ANNOTATION],
        response_format: Annotated[ResponseFormat, "Use this argument to control the amount of detail you need from this tool response."] = ResponseFormat.DETAILED,
    ) -> ToolResult:
        file_path = _FILE_MAP[document]

        try:
            reader = MdReader(str(file_path))
        except FileNotFoundError:
            raise ToolError(
                ErrorResponse(
                    title="File not found",
                    summary=f'Document "{document}" resolved to {file_path} but the file does not exist.',
                    invalid_value=document,
                    next_steps=["Ensure the mcp_server/data/ directory contains the expected .md files."],
                ).render()
            )

        rows = reader.list_sections()
        section_items = [SectionIndex(heading=name, word_count=wc, level=lvl) for name, wc, lvl in rows]

        def _heading_label(s: SectionIndex) -> str:
            prefix = ("#" * s.level + " ") if s.level > 0 else ""
            return f"{prefix}{s.heading}"

        if response_format == ResponseFormat.CONCISE:
            summary = SummaryResponse(
                summary=f"**{document}** has **{len(section_items)}** sections.",
                next_steps=[
                    NextStep(
                        tool_name=ToolNames.MD_QUERY,
                        description="Query a specific section by passing its heading as search_term",
                    ),
                ],
            )
        else:
            table_rows = "\n".join(f"| {_heading_label(s)} | {s.word_count} |" for s in section_items)
            table = f"| Section | Words |\n|---|---|\n{table_rows}"
            summary = SummaryResponse(
                summary=f"**{document}** has **{len(section_items)}** sections.",
                data_hint="Use a heading name (or key term from it) as search_term in md_query.",
                data_preview=table,
                next_steps=[
                    NextStep(
                        tool_name=ToolNames.MD_QUERY,
                        description="Query a specific section by passing its heading as search_term",
                    ),
                ],
            )

        return ToolResult(
            content=[TextContent(type="text", text=summary.render())],
            structured_content={"sections": [s.model_dump() for s in section_items]},
        )

    @mcp.tool(
        name=ToolNames.MD_QUERY,
        description=DOCSTRINGS["md_query"],
        annotations={
            "title": "Query Markdown Sections",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        tags={"documents", "context", "search"},
        output_schema=QueryResult.model_json_schema(),
    )
    @track_tool_execution
    async def md_query(
        document: Annotated[MdFileKey, _FILE_ANNOTATION],
        search_term: Annotated[str, "Keyword or phrase extracted from the user's question."],
        max_sections: Annotated[int, "Maximum number of sections to return (1–5)."] = Field(default=3, ge=1, le=5),
        response_format: Annotated[ResponseFormat, "Use this argument to control the amount of detail you need from this tool response."] = ResponseFormat.DETAILED,
    ) -> ToolResult:
        if not search_term.strip():
            raise ToolError(
                ErrorResponse(
                    title="Empty search term",
                    summary="search_term cannot be blank. Extract a keyword from the user's question.",
                    next_steps=["Identify the topic the user is asking about and pass it as search_term."],
                ).render()
            )

        file_path = _FILE_MAP[document]

        try:
            reader = MdReader(str(file_path))
        except FileNotFoundError:
            raise ToolError(
                ErrorResponse(
                    title="File not found",
                    summary=f'Document "{document}" resolved to {file_path} but the file does not exist.',
                    invalid_value=document,
                    next_steps=["Ensure the mcp_server/data/ directory contains the expected .md files."],
                ).render()
            )

        scored = reader.query(search_term, max_sections=max_sections)

        sections = [
            MatchedSection(
                heading=s.heading,
                content=s.content,
                word_count=len(s.content.split()),
            )
            for s in scored
        ]

        result = QueryResult(search_term=search_term, sections=sections)

        log_token_usage(
            tool_name=ToolNames.MD_QUERY,
            tool_id=search_term,
            data=result.model_dump(),
        )

        if not sections:
            summary = SummaryResponse(
                summary=f'No sections matched **"{search_term}"** in **{document}**.',
                warnings=["Try a broader or different search term."],
                next_steps=[
                    NextStep(
                        tool_name=ToolNames.MD_LIST_SECTIONS,
                        description="List all section headings to find the right term",
                    ),
                ],
            )
        elif response_format == ResponseFormat.CONCISE:
            summary = SummaryResponse(
                summary=f'Found **{len(sections)}** relevant section(s) for **"{search_term}"** in **{document}**.',
                highlights=[f"Top match: {sections[0].heading}"],
            )
        else:
            preview_lines = "\n".join(f"- **{s.heading}** ({s.word_count} words)" for s in sections)
            summary = SummaryResponse(
                summary=f'Found **{len(sections)}** relevant section(s) for **"{search_term}"** in **{document}**.',
                data_hint="sections contains the full text of each matched section — use it as context.",
                data_preview=preview_lines,
                highlights=[f"Top match: {sections[0].heading}"],
            )

        return ToolResult(
            content=[TextContent(type="text", text=summary.render())],
            structured_content=result.model_dump(),
        )
