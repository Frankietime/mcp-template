from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from mcp_shared import ErrorResponse, NextStep, ResponseFormat, SummaryResponse
from mcp_shared.logging import track_tool_execution
from mcp_shared.token_usage import log_token_usage
from toon_format import count_tokens, encode

from pydantic import Field

from .docstrings import DOCSTRINGS
from .schemas import ExampleOutputModel, FlatObjectArgument, NestedObjectArgument
from .tool_names import ToolNames

# ADD_TOOL PATTERN
#
# Each feature exports a single add_tool(mcp) function.
# The server's tool_box/__init__.py collects and calls them:
#
#   from features.my_feature.tool import add_tool as add_my_feature_tool
#
#   tools: list[Callable[[FastMCP], None]] = [
#       add_my_feature_tool,
#       add_other_tool,
#       ...
#   ]
#   for tool in tools:
#       tool(mcp)
#
# Benefits:
# - Enable/disable tools by adding/removing from the list
# - Each feature is self-contained and independently deployable


def add_tool(mcp: FastMCP) -> None:  # noqa: ARG001
    raise NotImplementedError(
        "_tools_template is a reference template and must not be registered with the MCP server. "
        "Copy it to a new feature directory instead."
    )

    @mcp.tool(
        # the @mcp.tool decorator exposes a series of arguments that can be used
        # as metadata for agent guidance and system information.
        # The following are some examples of arguments provided by FastMCP.

        name=ToolNames.TOOL_TEMPLATE,  # Use ToolNames registry constants instead of inline strings.
        enabled=True,  # Currently deprecated in newer versions of FastMCP
        meta={"version": "1.0", "author": "your-team"},  # Custom metadata for versioning and app-specific purposes
        # timeout=10,  # Tool execution timeout — not supported in FastMCP <3.0.0; re-enable when upgrading

        # DOCSTRINGS / DESCRIPTIONS
        #
        # We use a registry pattern to manage docstrings separately from tool logic.
        # See ./docstrings/ folder for versioned docstrings.
        # The active version is set in docstrings/__init__.py
        #
        # Benefits:
        # - Version control: track docstring evolution separately from logic changes
        # - A/B testing: swap versions to test which docstring performs better with agents
        # - Centralized: all LLM-facing text in one place for easy refinement
        #
        # PROMPT-ENGINEERING
        #
        # Use prompt-engineering best practices for writing effective docstrings.
        # https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use#best-practices-for-tool-definitions
        description=DOCSTRINGS["tool_template"],  # Loaded from docstrings registry (see ./docstrings/)

        # ANNOTATIONS
        #
        # Annotations are useful for agent's decision making, they inform the agent about the effects of using the tool.
        # For example, clients such as Claude or ChatGPT will ask for permission when
        # trying to execute a tool marked as 'destructiveHint=True'
        annotations={
            "title": "Resource Info Tool",
            "readOnlyHint": True,    # readOnly tools do not modify data.
            "destructiveHint": False,  # Indicates if this tool performs destructive actions.

            # Indicates that multiple calls with the same arguments will yield the same result.
            "idempotentHint": True,  # This is VERY useful because Agents often retry on failure.
            "openWorldHint": False,  # Indicates whether this tool interacts with outside systems.
        },

        # TAGS
        #
        # Tags for organization/filtering, makes it possible to activate/deactivate groups of tools and generate
        # a mod-like system to test different tool combinations and sets, or deploy specific combinations
        # while keeping the whole system untouched. (fastmcp 3.0.0+)
        tags={"resources", "search"},

        # OUTPUT SCHEMAS
        #
        # This is the expected output schema for structured_content (see below the function return object).
        # This prevents the model from hallucinating fields that don't exist and is used for validation purposes.
        #
        # RECOMMENDED: Let FastMCP infer from return type annotation (auto-wraps non-objects):
        #   async def my_tool(...) -> ExampleOutputModel:      # Object - no wrapping needed
        #   async def my_tool(...) -> list[ExampleOutputModel]:  # Auto-wrapped as {"result": [...]}
        #
        # EXPLICIT SCHEMAS (when needed): MCP spec requires object types.
        # If providing explicit schema, you must wrap non-objects yourself:
        #   output_schema={
        #       "type": "object",
        #       "properties": {
        #           "resources": {"type": "array", "items": ExampleOutputModel.model_json_schema()}
        #       },
        #       "required": ["resources"]
        #   }
        #   # Then structured_content must match: {"resources": [...]}
        #
        # Use explicit schemas when you need custom property names or schema tweaks.
        output_schema=ExampleOutputModel.model_json_schema()  # Object type - valid as-is
    )
    # TOOL NAMES AND NAMESPACING
    #
    # By selectively implementing tools whose names reflect natural subdivisions of tasks,
    # you simultaneously reduce the number of tools and tool descriptions loaded into the agent's context
    # and offload agentic computation from the agent's context back into the tool calls themselves.
    #
    # On the other hand, correctly namespacing your tool with a prefix or suffix
    # has non-trivial effects when agents need to choose tools between multiple MCP Servers.
    #
    # Choose a consistent prefix (e.g., your server name) when creating tools.
    @track_tool_execution  # This decorator provides basic tool execution logging
    async def mcp_tool_template(

        # ANNOTATED VS NON-ANNOTATED ARGUMENTS
        #
        # Models tend to grasp the meaning of a well named argument better than reading the annotation.
        # Because of their 'attention' mechanism, they prioritize the first tokens which in this case are argument names, annotations come later.
        resource_id: int,  # Adding further description here is redundant and adds tokens.
        resource_tags: Annotated[list[str], "A brief explanation on how this input impacts the resource may prove useful here."],

        # SIMPLE & FLATTEN ARGUMENTS
        #
        # Avoid nested or complex objects as arguments. Instead prefer primitives/literals and flat objects only with the required fields for the task.
        # Models tend to get confused when creating or exploring nested structures and benefit from flat objects and tabular-like data.
        #
        # Avoid:
        nested_argument: Annotated[NestedObjectArgument, "Nested data may be useful for certain tasks, but always default to flat objects when possible."],
        # Prefer:
        flat_argument: Annotated[FlatObjectArgument, "Models perform better when asked to pass or read a simple object or list of flat objects."],

        # LITERAL ENUMS
        #
        # Literal enums are ad-hoc enums that limit the range of choices an agent has for calling tool arguments.
        # It generates predictable inputs that can be safely used inside the tool, saving validation logic.
        # Also, using literal enums reduces cognitive load for other developers since these enums shouldn't have any impact outside this tool.
        operation_type: Literal["read", "summarize", "export"],

        # DEFINED ENUMS
        #
        # On the other hand, as always, enums defined in the codebase are useful when
        # the argument options are shared across multiple tools or have a broader meaning in the codebase.
        response_format: Annotated[ResponseFormat, "Use this argument to control the amount of detail (and therefore token usage) you need from this tool response."],
        #
        # A practical use-case for enums in tools is to give agents flexibility to select
        # tool output verbosity, low-level details or even content structure by switching between different response formats.
        # This also allows you to control token usage and be in compliance with the tool's defined token budget.
        #
        # CONCISE should return truncated data (maybe no more than 5 rows), a brief description of what happened and what to do next
        # DETAILED may return the full data object (another truncation may be performed anyway to avoid blowing context window), a detailed description of what happened and next steps.
        # VERBOSE_DEBUG may return the full data object without truncation, and also apply logging and other useful information for debugging purposes.

        # ARGUMENT VALIDATION: Pydantic Models & Fields
        #
        # Always use Pydantic Models for object arguments and Fields for python literals to enable automatic validation.
        # FastMCP uses Pydantic's flexible validation to check inputs vs your type annotations.
        # 'Field' objects let you define custom constraints.
        #
        # For example:
        # The use of 'Field' validates that the input is greater or equal than 0.0 and less or equal than 1.0.
        confidence_threshold: float = Field(description="Minimum confidence score for results", ge=0.0, le=1.0),

    ) -> ToolResult:  # return type (see below for details on ToolResult)

        # Token Budget Allocation
        #
        # It's important to have in mind a max. number of tokens to be returned by the tool,
        # either just for design purposes or to be directly monitored and controlled by guardrails that perform
        # truncations or error responses when limits are exceeded.
        #
        # For example, Claude Code tool responses are restricted to 25,000 tokens by default.

        # Token Usage Monitoring
        #
        # Currently, we use the following methods from the toon-format library to monitor token usage:

        resource_data: dict = {
            "id": resource_id,
            "name": "Example Resource",
            "status": "active",
            "tags": resource_tags,
            "metadata": {
                "created_at": "2026-01-01T00:00:00Z",
                "confidence": confidence_threshold,
                "operation": operation_type,
            },
        }

        encoded_resource = encode(resource_data)  # encode a value into TOON format (string)
        json_token_count = count_tokens(str(resource_data))
        toon_token_count = count_tokens(encoded_resource)

        # You can use report utils to log token usage and make comparisons
        # between JSON and TOON formatting for the same data.
        # The following log method outputs to console and maintains a markdown file report.
        #
        # Results have shown a ~20% token reduction when using TOON format vs original JSON format.
        log_token_usage(
            tool_name="mcp_tool_template",
            tool_id=str(resource_id),
            data=resource_data,
        )

        # ERRORS
        #
        # Error communication is an opportunity to provide further information or instructions dynamically, only when required,
        # as opposed to the upfront context information provided when a Client connects to the MCP Server.
        #
        # Error messages should summarize the ongoing error, provide next steps and
        # additional documentation that's required only when an error happens.
        # This approach guides the agent towards a better understanding and use of our MCP Server.
        #
        # Use ErrorResponse (from mcp_shared) to build structured error messages.
        # In combination with the ResponseFormat input enum, we can control error verbosity:
        # - CONCISE: minimal error info
        # - DETAILED: full error with examples and next steps
        # - VERBOSE_DEBUG: includes additional debug context

        if resource_data is None:  # or any other condition that indicates an error
            if response_format == ResponseFormat.CONCISE:
                raise ToolError(ErrorResponse(
                    title="Resource Not Found",
                    summary=f"Resource ID `{resource_id}` does not exist.",
                ).render())
            elif response_format == ResponseFormat.VERBOSE_DEBUG:
                raise ToolError(ErrorResponse(
                    title="Resource Not Found",
                    summary=f"Resource ID `{resource_id}` does not exist or is in the wrong format.",
                    invalid_value=str(resource_id),
                    valid_examples=["1928", "9381"],
                    next_steps=[
                        "Call `list_resources()` to find valid resource IDs",
                        "Verify the resource ID is an integer",
                        "Check if the resource was recently deleted",
                    ],
                ).render())
            else:  # DETAILED (default)
                raise ToolError(ErrorResponse(
                    title="Resource Not Found",
                    summary=f"Resource ID `{resource_id}` does not exist.",
                    invalid_value=str(resource_id),
                    valid_examples=["1928", "9381"],
                    next_steps=["Call `list_resources()` to find valid resource IDs"],
                ).render())

        # TOOL RESULTS
        #
        # The ToolResult class lets you have granular control over the structure and content of the tool response as well as
        # control over token usage, leverage the response as a 'next prompt', specify next steps to follow, etc.
        #
        # SUMMARY RESPONSE
        #
        # Use SummaryResponse (from mcp_shared) to build the markdown text for ToolResult.content.
        # It renders a structured, token-efficient markdown string that guides the agent's next decision.
        # Only non-empty sections are rendered. The only required field is `summary`.
        #
        # Sections (rendered in order, skipped when empty):
        #   1. summary           — what happened (required)
        #   2. data_hint         — what structured_content contains
        #   3. truncation_notice — if data was cut
        #   4. data_preview      — pre-rendered markdown (table, bullets, etc.)
        #   5. highlights        — aggregate stats or key takeaways
        #   6. next_steps        — workflow guidance via NextStep(tool_name, description)
        #   7. warnings          — validation issues, partial failures
        #
        # See packages/mcp_shared/summary_response.py for full implementation.

        # --- Simple usage: just a summary string ---
        # summary = SummaryResponse(summary="Resource 1928 retrieved successfully.")

        # --- ResponseFormat controls summary verbosity ---
        tag_count = len(resource_data.get("tags", []))

        # In combination with the ResponseFormat input enum, we can control the amount of detail provided and overall token usage
        if response_format == ResponseFormat.CONCISE:
            # Minimal response: just the essential summary
            summary = SummaryResponse(
                summary=f"Found resource `{resource_data['name']}` with **{tag_count}** tag(s).",
                next_steps=[NextStep(tool_name="get_resource_by_id", description="View full details")],
            )
        elif response_format == ResponseFormat.VERBOSE_DEBUG:
            # Full response with all sections populated
            summary = SummaryResponse(
                summary=f"Found resource `{resource_data['name']}` with **{tag_count}** tag(s).",
                data_hint="Full data in structured_content. Fields: id, name, status, tags, metadata.",
                truncation_notice="Showing first 3 of 10 results" if tag_count > 3 else None,
                data_preview=(
                    "| id     | name             | status |\n"
                    "|--------|------------------|--------|\n"
                    "| 1928   | Example Resource | active |"
                ),
                highlights=[
                    f"Resource ID: {resource_id}",
                    f"Operation: {operation_type}",
                    f"Token count (JSON): {json_token_count}",
                    f"Token count (TOON): {toon_token_count}",
                ],
                next_steps=[
                    NextStep(tool_name="get_resource_by_id", description="View full details of a specific resource"),
                    NextStep(tool_name="list_resources", description="Browse all available resources"),
                ],
                warnings=["Confidence below threshold"] if confidence_threshold < 0.5 else [],
            )
        else:  # DETAILED (default)
            summary = SummaryResponse(
                summary=f"Found resource `{resource_data['name']}` with **{tag_count}** tag(s).",
                data_hint="Default display: id, name, status.",
                data_preview=(
                    "| id     | name             | status |\n"
                    "|--------|------------------|--------|\n"
                    "| 1928   | Example Resource | active |"
                ),
                highlights=[
                    f"Resource ID: {resource_id}",
                    f"Operation: {operation_type}",
                ],
                next_steps=[
                    NextStep(tool_name="get_resource_by_id", description="View full details of a specific resource"),
                    NextStep(tool_name="list_resources", description="Browse all available resources"),
                ],
                warnings=["Confidence below threshold"] if confidence_threshold < 0.5 else [],
            )

        return ToolResult(
            content=[
                # SummaryResponse.render() produces a markdown string for the agent.
                TextContent(type="text", text=summary.render()),
                # Non-text content types are still added directly — SummaryResponse only handles text.
                # ImageContent(type="image", data="base64...", mimeType="image/png")
            ],

            # A dictionary containing structured data that matches your tool's output schema.
            # This enables clients to programmatically process the results.
            # Beware of the tool's allocated token budget when returning structured content.
            structured_content=resource_data,  # Must match output_schema structure
            meta={
                # Typically ignored by LLMs, used for system-to-system communication.
                # It comprises runtime metadata about the tool execution.
                # Use this for performance metrics, telemetry, debugging information, UI hints/info, pagination, auth flow,
                # or any client-specific data that doesn't belong in the content or structured output.
                "execution_time_ms": 145,
                "model_version": "1.0",
                "confidence": confidence_threshold,
                "token_usage": json_token_count,
            },
        )
