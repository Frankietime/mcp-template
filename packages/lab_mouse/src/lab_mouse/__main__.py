"""Terminal UI entry point — ``uv run agent``."""

import asyncio
from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    for parent in [Path.cwd(), *Path.cwd().parents]:
        env_file = parent / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            return


_load_env()

from .deps import AgentDeps  # noqa: E402
from .session import AgentSession  # noqa: E402
from .tui.app import AgentTuiApp  # noqa: E402


async def _run(deps: AgentDeps) -> None:
    session = AgentSession(deps)
    await AgentTuiApp(session, deps).run()


def main() -> None:
    """Entry point for ``uv run agent``."""
    try:
        asyncio.run(_run(AgentDeps()))
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()
