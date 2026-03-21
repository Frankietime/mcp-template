"""Terminal chat REPL — ``uv run agent``."""

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

from rich.console import Console  # noqa: E402
from rich.markdown import Markdown  # noqa: E402
from rich.prompt import Prompt  # noqa: E402

from .agent import create_agent  # noqa: E402
from .deps import AgentDeps  # noqa: E402

console = Console()


async def _chat(deps: AgentDeps) -> None:
    """Run an interactive multi-turn chat loop against the MCP agent.

    Args:
        deps: Runtime configuration used to build the agent.
    """
    agent = create_agent(deps)
    messages: list = []
    console.print(f"[bold green]Agent ready[/] ([dim]{deps.model}[/]). Type 'exit' to quit.\n")
    async with agent.run_mcp_servers():
        while True:
            user_input = Prompt.ask("[bold cyan]You[/]")
            if user_input.strip().lower() in ("exit", "quit", "q"):
                break
            with console.status("[dim]Thinking…[/]"):
                result = await agent.run(
                    user_input,
                    deps=deps,
                    message_history=messages,
                    model=deps.model,                        # (1) per-call model — enables runtime switching
                    model_settings={"temperature": 0.3},    # (2) temperature
                )
            messages = result.all_messages()
            console.print("[bold green]Agent[/]")
            console.print(Markdown(result.output))
            console.print()


def main() -> None:
    """Entry point for ``uv run agent``."""
    asyncio.run(_chat(AgentDeps()))


if __name__ == "__main__":
    main()
