"""SummaryResponse — Builds markdown summaries for ToolResult.content.

Renders a structured, token-efficient markdown string that guides the agent's
next decision. Only non-empty sections are rendered.

Usage:
    # Simple — just a string
    summary = SummaryResponse(summary="Item 1928 updated successfully.")

    # Rich — add what you need
    summary = SummaryResponse(
        summary="Found **12** item(s).",
        data_hint="Default display: Id, Name, Type, Status.",
        next_steps=[NextStep(tool_name="get_item_by_id", description="View full details")],
    )

    # Use in ToolResult
    return ToolResult(
        content=[TextContent(type="text", text=summary.render())],
        structured_content={...},
    )
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class NextStep(BaseModel):
    """A suggested next action for the agent."""

    tool_name: str = Field(..., description="Tool name from ToolNames registry")
    description: str = Field(..., description="Why or when to use this tool next")


class SummaryResponse(BaseModel):
    """Builds a markdown summary string for ToolResult.content.

    Renders sections in order (only non-empty sections appear):
    1. summary            — what happened (only required field)
    2. data_hint          — what the structured_content contains
    3. truncation_notice  — if data was cut
    4. data_preview       — pre-rendered markdown (table, bullets, etc.)
    5. highlights         — aggregate stats or key takeaways
    6. next_steps         — workflow guidance for the agent
    7. warnings           — validation issues, partial failures
    """

    summary: str = Field(..., description="Concise outcome: what happened")
    data_hint: str | None = Field(default=None, description="Describes structured_content shape")
    truncation_notice: str | None = Field(default=None, description="E.g. 'Showing first 5 of 42'")
    data_preview: str | None = Field(default=None, description="Pre-rendered markdown table or bullets")
    highlights: list[str] = Field(default_factory=list, description="Key stats or takeaways")
    next_steps: list[NextStep] = Field(default_factory=list, description="Suggested next tool calls")
    warnings: list[str] = Field(default_factory=list, description="Validation issues or caveats")

    def render(self) -> str:
        """Render to a markdown string for TextContent."""
        sections: list[str] = []

        sections.append(self.summary)

        if self.data_hint:
            sections.append(self.data_hint)

        if self.truncation_notice:
            sections.append(f"_{self.truncation_notice}_")

        if self.data_preview:
            sections.append(self.data_preview)

        if self.highlights:
            sections.append("\n".join(f"- {h}" for h in self.highlights))

        if self.next_steps:
            steps = "\n".join(
                f"- **{ns.description}**: `{ns.tool_name}`" for ns in self.next_steps
            )
            sections.append(f"**Next steps:**\n{steps}")

        if self.warnings:
            warns = "\n".join(f"- {w}" for w in self.warnings)
            sections.append(f"⚠ **Warnings:**\n{warns}")

        return "\n\n".join(sections)
