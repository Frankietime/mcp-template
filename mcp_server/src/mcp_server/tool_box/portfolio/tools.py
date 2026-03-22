from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from mcp_shared import ErrorResponse, NextStep, SummaryResponse
from mcp_shared.logging import track_tool_execution

from .docstrings import DOCSTRINGS
from .loader import get_portfolio
from .schemas import SearchMatch, SearchResult, SectionContent, SectionItem
from .tool_names import ToolNames


def add_tool(mcp: FastMCP) -> None:
    """Register all portfolio tools with the MCP server."""

    @track_tool_execution
    @mcp.tool(
        name=ToolNames.PORTFOLIO_GET_SUMMARY,
        description=DOCSTRINGS["portfolio_get_summary"],
        annotations={
            "title": "Portfolio Summary",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        tags={"portfolio", "profile"},
        output_schema=SectionContent.model_json_schema(),
    )
    async def portfolio_get_summary() -> ToolResult:
        portfolio = get_portfolio()
        name, content = portfolio.get_summary()

        if not content:
            raise ToolError(
                ErrorResponse(
                    title="Portfolio is empty",
                    summary="The portfolio file was loaded but contains no readable content.",
                    next_steps=[
                        "Edit mcp_server/data/RESUME.md and add your profile information.",
                        "Call portfolio_list_sections() to verify the file was parsed correctly.",
                    ],
                ).render()
            )

        summary = SummaryResponse(
            summary=f"Profile summary from section **{name}**.",
            data_hint="This is the introductory section of the portfolio.",
            data_preview=content[:400] + ("…" if len(content) > 400 else ""),
            next_steps=[
                NextStep(tool_name=ToolNames.PORTFOLIO_LIST_SECTIONS, description="See all available sections"),
                NextStep(tool_name=ToolNames.PORTFOLIO_SEARCH, description="Search for specific information"),
            ],
        )

        return ToolResult(
            content=[TextContent(type="text", text=summary.render())],
            structured_content=SectionContent(
                name=name,
                content=content,
                word_count=len(content.split()),
            ).model_dump(),
        )

    @track_tool_execution
    @mcp.tool(
        name=ToolNames.PORTFOLIO_LIST_SECTIONS,
        description=DOCSTRINGS["portfolio_list_sections"],
        annotations={
            "title": "List Portfolio Sections",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        tags={"portfolio", "discovery"},
        output_schema={
            "type": "object",
            "properties": {
                "sections": {
                    "type": "array",
                    "items": SectionItem.model_json_schema(),
                }
            },
            "required": ["sections"],
        },
    )
    async def portfolio_list_sections() -> ToolResult:
        portfolio = get_portfolio()
        sections = portfolio.list_sections()

        rows = "\n".join(f"| {name} | {wc} |" for name, wc in sections)
        table = f"| Section | Words |\n|---|---|\n{rows}"

        section_items = [SectionItem(name=name, word_count=wc) for name, wc in sections]

        summary = SummaryResponse(
            summary=f"Found **{len(sections)}** sections in the portfolio.",
            data_hint="Use portfolio_get_section(section_name=...) to read any section.",
            data_preview=table,
            next_steps=[
                NextStep(tool_name=ToolNames.PORTFOLIO_GET_SECTION, description="Read a specific section"),
                NextStep(tool_name=ToolNames.PORTFOLIO_SEARCH, description="Search across all sections"),
            ],
        )

        return ToolResult(
            content=[TextContent(type="text", text=summary.render())],
            structured_content={"sections": [s.model_dump() for s in section_items]},
        )

    @track_tool_execution
    @mcp.tool(
        name=ToolNames.PORTFOLIO_GET_SECTION,
        description=DOCSTRINGS["portfolio_get_section"],
        annotations={
            "title": "Get Portfolio Section",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        tags={"portfolio"},
        output_schema=SectionContent.model_json_schema(),
    )
    async def portfolio_get_section(
        section_name: Annotated[str, "The section heading to retrieve (case-insensitive, prefix match supported)."],
    ) -> ToolResult:
        portfolio = get_portfolio()
        result = portfolio.get_section(section_name)

        if result is None:
            available = [name for name, _ in portfolio.list_sections()]
            raise ToolError(
                ErrorResponse(
                    title="Section not found",
                    summary=f'No section matching "{section_name}" was found in the portfolio.',
                    invalid_value=section_name,
                    valid_examples=available[:5],
                    next_steps=["Call portfolio_list_sections() to see all available sections."],
                ).render()
            )

        name, content = result

        summary = SummaryResponse(
            summary=f"Section **{name}** ({len(content.split())} words).",
            data_preview=content[:600] + ("…" if len(content) > 600 else ""),
            next_steps=[
                NextStep(tool_name=ToolNames.PORTFOLIO_SEARCH, description="Search for something specific"),
                NextStep(tool_name=ToolNames.PORTFOLIO_LIST_SECTIONS, description="Browse other sections"),
            ],
        )

        return ToolResult(
            content=[TextContent(type="text", text=summary.render())],
            structured_content=SectionContent(
                name=name,
                content=content,
                word_count=len(content.split()),
            ).model_dump(),
        )

    @track_tool_execution
    @mcp.tool(
        name=ToolNames.PORTFOLIO_SEARCH,
        description=DOCSTRINGS["portfolio_search"],
        annotations={
            "title": "Search Portfolio",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        tags={"portfolio", "search"},
        output_schema=SearchResult.model_json_schema(),
    )
    async def portfolio_search(
        query: Annotated[str, "Keyword or phrase to search for across the entire portfolio."],
    ) -> ToolResult:
        if not query.strip():
            raise ToolError(
                ErrorResponse(
                    title="Empty query",
                    summary="The search query cannot be empty.",
                    next_steps=["Provide a keyword, skill, technology, or company name to search for."],
                ).render()
            )

        portfolio = get_portfolio()
        raw_matches = portfolio.search(query)

        if not raw_matches:
            summary = SummaryResponse(
                summary=f'No matches found for **"{query}"**.',
                next_steps=[
                    NextStep(tool_name=ToolNames.PORTFOLIO_LIST_SECTIONS, description="Browse available sections instead"),
                ],
            )
            return ToolResult(
                content=[TextContent(type="text", text=summary.render())],
                structured_content=SearchResult(query=query, total_matches=0, matches=[]).model_dump(),
            )

        matches = [SearchMatch(section=section, excerpt=excerpt) for section, excerpt in raw_matches]

        rows = "\n".join(f"| {m.section} | {m.excerpt[:80]}… |" for m in matches[:10])
        table = f"| Section | Excerpt |\n|---|---|\n{rows}"

        summary = SummaryResponse(
            summary=f'Found **{len(matches)}** match(es) for **"{query}"**.',
            data_hint="Excerpts are ~240 characters centred on the match.",
            data_preview=table,
            next_steps=[
                NextStep(tool_name=ToolNames.PORTFOLIO_GET_SECTION, description="Read a full section"),
            ],
        )

        return ToolResult(
            content=[TextContent(type="text", text=summary.render())],
            structured_content=SearchResult(
                query=query,
                total_matches=len(matches),
                matches=matches,
            ).model_dump(),
        )
