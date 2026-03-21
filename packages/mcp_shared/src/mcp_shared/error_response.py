# mcp_shared/error_response.py
"""Structured error message builder for ToolError."""

from dataclasses import dataclass, field


@dataclass
class ErrorResponse:
    """Structured error message builder for ToolError.

    Renders a consistent, agent-friendly markdown error message.
    Only non-empty sections are rendered.

    Usage:
        from fastmcp.exceptions import ToolError
        from mcp_shared import ErrorResponse

        raise ToolError(ErrorResponse(
            title="Resource Not Found",
            summary=f"Item ID `{item_id}` does not exist.",
            invalid_value=str(item_id),
            valid_examples=["1928", "9381"],
            next_steps=["Call `list_resources()` to find valid IDs"]
        ).render())
    """

    title: str                              # e.g., "Resource Not Found", "Invalid Input"
    summary: str                            # What went wrong
    invalid_value: str | None = None        # The bad input value
    valid_examples: list[str] = field(default_factory=list)  # Example valid values
    next_steps: list[str] = field(default_factory=list)      # How to resolve

    def render(self) -> str:
        """Render error as markdown string."""
        sections = [f"# {self.title}", "", "## Error Summary", self.summary]

        if self.invalid_value:
            sections.extend(["", f"**Invalid Input:** `{self.invalid_value}`"])

        if self.valid_examples:
            sections.extend(["", "## Valid Examples"])
            sections.extend([f"- `{v}`" for v in self.valid_examples])

        if self.next_steps:
            sections.extend(["", "## Next Steps"])
            sections.extend([f"- {s}" for s in self.next_steps])

        return "\n".join(sections)
