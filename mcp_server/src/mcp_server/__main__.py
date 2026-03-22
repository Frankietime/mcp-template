import asyncio
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastmcp.server import FastMCP
from mcp_shared.config import get_settings

from .instructions import register_instructions
from .tool_box import register_all_tools
from .tool_box.portfolio.loader import load_portfolio

# Load environment variables from .env for local development
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Application lifespan context manager.

    Use this to initialize and clean up resources (DB connections, caches, etc.)
    that should live for the duration of the server's lifetime.

    Example — add auth on startup:
        import os
        from my_auth import AuthProvider
        secret = os.getenv("API_SECRET")
        if not secret:
            raise RuntimeError("API_SECRET environment variable is required")
        auth = AuthProvider(secret=secret)
        await auth.initialize()

    Yield:
        await auth.close()
    """
    logger.info("MCP Template Server starting up.")

    default_path = str(Path(__file__).parent.parent.parent / "data" / "RESUME.md")
    md_path = os.getenv("PORTFOLIO_MD_PATH", default_path)
    portfolio = load_portfolio(md_path)
    logger.info("Portfolio loaded from %s — %d section(s)", portfolio.source_path, portfolio.section_count)

    yield
    logger.info("MCP Template Server shutting down.")


mcp = FastMCP(
    name="mcp_template_server",
    lifespan=app_lifespan,

    # MCP Server instructions are not yet supported by all agent frameworks
    # (e.g. Google ADK, Pydantic AI). Re-enable when your target framework supports it.
    # instructions=MCP_SERVER_INSTRUCTIONS,

    # --- OPTIONAL: Rate limiting (uncomment and configure as needed) ---
    # from my_rate_limiter import RateLimitingMiddleware
    # middleware=[RateLimitingMiddleware(capacity=100, refill_rate=20.0)]
)

_settings = get_settings()
logger.info("Environment: %s | Features: %s", _settings.app_env, _settings.features.model_dump())

register_instructions(mcp)
register_all_tools(mcp, _settings)


# --- OPTIONAL: Selective tool visibility (fastmcp 3.0.0+) ---
# mcp.disable(tags={}, keys={"tool:read_mcp_instructions"})
# mcp.enable(tags={}, keys={})


async def _async_main() -> None:
    """Run the MCP server."""
    await mcp.run_async(transport="streamable-http")


def main() -> None:
    """Entry point for the MCP server."""
    logger.info("Starting MCP Template Server")
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
