"""Unit tests for mcp_shared response builders."""

from mcp_shared import ErrorResponse, NextStep, SummaryResponse


class TestErrorResponse:
    def test_render_title_and_summary(self) -> None:
        err = ErrorResponse(title="Not Found", summary="Resource does not exist.")
        rendered = err.render()
        assert "# Not Found" in rendered
        assert "Resource does not exist." in rendered

    def test_render_with_all_fields(self) -> None:
        err = ErrorResponse(
            title="Invalid Input",
            summary="The provided ID is not valid.",
            invalid_value="abc",
            valid_examples=["1928", "9381"],
            next_steps=["Call list_resources() to find valid IDs"],
        )
        rendered = err.render()
        assert "**Invalid Input:** `abc`" in rendered
        assert "- `1928`" in rendered
        assert "- `9381`" in rendered
        assert "- Call list_resources() to find valid IDs" in rendered

    def test_render_omits_empty_sections(self) -> None:
        err = ErrorResponse(title="Error", summary="Something went wrong.")
        rendered = err.render()
        assert "Valid Examples" not in rendered
        assert "Next Steps" not in rendered


class TestSummaryResponse:
    def test_render_summary_only(self) -> None:
        s = SummaryResponse(summary="Operation completed successfully.")
        assert s.render() == "Operation completed successfully."

    def test_render_with_next_steps(self) -> None:
        s = SummaryResponse(
            summary="Found 3 resources.",
            next_steps=[NextStep(tool_name="get_resource_by_id", description="View full details")],
        )
        rendered = s.render()
        assert "Found 3 resources." in rendered
        assert "get_resource_by_id" in rendered
        assert "View full details" in rendered

    def test_render_omits_empty_sections(self) -> None:
        s = SummaryResponse(summary="Done.")
        rendered = s.render()
        assert "Next steps:" not in rendered
        assert "Warnings:" not in rendered

    def test_render_warnings(self) -> None:
        s = SummaryResponse(summary="Done.", warnings=["Low confidence score"])
        rendered = s.render()
        assert "Low confidence score" in rendered
