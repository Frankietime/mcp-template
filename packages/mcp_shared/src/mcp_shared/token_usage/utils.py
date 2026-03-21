# mcp_shared/token_usage/utils.py
"""TOON format utilities for token optimization.

TOON is a compact serialization format that reduces token usage when sending data to LLMs.
"""

import os

from rich.console import Console
from rich.table import Table
from toon_format import count_tokens, encode


def log_token_usage(tool_name: str, tool_id: str, data: dict) -> None:
    """Log token usage comparison between TOON and JSON formats.

    Outputs to console (Rich table) and appends to token_usage_comparison.md file.

    Args:
        tool_name: Name of the tool being logged
        tool_id: Identifier for the specific call (e.g., resource_id or count)
        data: Dictionary data to compare encoding sizes
    """
    encoded = encode(data)
    json_token_count = count_tokens(str(data))
    toon_token_count = count_tokens(encoded)

    table = Table(title="Token Usage Comparison")
    table.add_column("Tool", style="green")
    table.add_column("ID", style="green")
    table.add_column("TOON", style="cyan")
    table.add_column("JSON", style="magenta")
    table.add_column("% Diff", style="yellow")

    percentage_diff = ((json_token_count - toon_token_count) / json_token_count) * 100 if json_token_count > 0 else 0
    diff_sign = "+" if percentage_diff >= 0 else ""

    table.add_row(
        tool_name,
        str(tool_id),
        str(toon_token_count),
        str(json_token_count),
        f"{diff_sign}{percentage_diff:.1f}%",
    )

    Console().print(table)
    _append_to_markdown(tool_name, tool_id, toon_token_count, json_token_count, percentage_diff)


def _append_to_markdown(
    tool_name: str,
    tool_id: str,
    toon_tokens: int,
    json_tokens: int,
    percentage_diff: float,
) -> None:
    """Append token comparison row to markdown file."""
    md_file = "token_usage_comparison.md"
    diff_sign = "+" if percentage_diff >= 0 else ""

    rows = []
    if os.path.exists(md_file):
        with open(md_file) as f:
            lines = f.read().strip().split("\n")
            for line in lines[2:]:  # Skip header and separator
                if line.strip() and line.startswith("|"):
                    cols = [col.strip() for col in line.split("|")[1:-1]]
                    if cols:
                        rows.append(cols)

    rows.append([
        tool_name,
        str(tool_id),
        str(toon_tokens),
        str(json_tokens),
        f"{diff_sign}{percentage_diff:.1f}%",
    ])

    with open(md_file, "w") as f:
        f.write("| Tool | ID | TOON | JSON | % Diff |\n")
        f.write("|------|-----|------|------|--------|\n")
        for row in rows:
            f.write(f"| {' | '.join(row)} |\n")
