from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from mcp_server.instructions.instructions import MCP_SERVER_INSTRUCTIONS


def register_instructions(mcp: FastMCP) -> None:
    """Register the healthcheck route and instructions tool."""

    @mcp.custom_route("/healthcheck", methods=["GET"])
    async def health_check(request: Request) -> PlainTextResponse:
        return PlainTextResponse("OK")

    @mcp.tool(
        # tags={"instructions"}
        enabled=False,
    )
    async def read_mcp_instructions() -> str:
        """ALWAYS run this tool first before any interaction with the user.
        This is the most important tool, read the returned instructions carefully before doing anything else.
        This tool shows you how the MCP server works, what tools are available and when to use them.
        """
        return MCP_SERVER_INSTRUCTIONS
