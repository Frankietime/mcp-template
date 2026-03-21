# MCP Server Template

A generic, production-ready scaffold for building [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers with Python and [FastMCP](https://github.com/jlowin/fastmcp).

This template preserves the architecture, patterns, and best practices of a real production MCP server — stripped of all domain-specific code so you can fork it and build your own.

---

## Architecture

```
mcp-template/
├── packages/
│   ├── agent/              # Pydantic-AI terminal chat agent for local testing
│   └── mcp_shared/         # Shared utilities (response builders, schemas, logging)
├── mcp_server/             # Main MCP Server
│   └── src/mcp_server/
│       ├── __main__.py          # Server entry point
│       ├── instructions/        # Agent instructions (4-layer framework)
│       ├── tool_box/            # Tool registration + _tools_template reference
│       └── workflows/           # Multi-step workflow orchestration
├── src/mcp_workspace/      # Workspace root package
├── tests/
│   ├── unit/               # Unit tests for packages
│   └── agentic/            # Agentic integration tests (requires running server)
└── docs/                   # Architecture and best practices documentation
```

### Key Design Decisions

- **`mcp_shared`** — All tools use shared response builders (`SummaryResponse`, `ErrorResponse`) and `ResponseFormat` enum to control output verbosity and token usage.
- **`_tools_template`** — A fully annotated reference implementation. Every architectural decision is documented inline. Read this before creating your first tool.
- **Docstring Registry** — Tool descriptions are versioned separately from logic, enabling A/B testing and prompt engineering without touching business logic.
- **ToolNames Registry** — All tool names are constants. No inline strings — prevents typos and enables safe IDE refactors.
- **TOON Format** — Token-optimized serialization for structured data in tool responses (`toon-format` library).

---

## Setup

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

### Install

```bash
# Clone and install all workspace packages
git clone <your-repo-url> mcp-template
cd mcp-template
uv sync --all-packages
```

### Configure environment

```bash
cp .env.sample .env
# Edit .env with your settings (no required values for basic local usage)
```

---

## Running the Server

```bash
uv run mcp_server
```

The server starts at `http://127.0.0.1:8000/mcp/` (streamable HTTP transport).

### Health check

```bash
curl http://127.0.0.1:8000/healthcheck
# → OK
```

### Debug with MCP Inspector

```bash
npx @modelcontextprotocol/inspector http://127.0.0.1:8000/mcp/
```

Open `http://localhost:6274` in your browser. You should see the `mcp_tool_template` tool registered.

### Run the Pydantic-AI Agent

```bash
# Start server first, then in a second terminal:
uv run agent
```

This starts an interactive terminal chat REPL connected to your local MCP server.

---

## Running Tests

```bash
uv run pytest
```

Agentic tests (require a running server) are skipped by default. To run them:
```bash
# Terminal 1: start the server
uv run mcp_server

# Terminal 2: run agentic tests
uv run pytest tests/agentic/ -v
```

---

## How to Create a New Tool

1. **Create a feature folder** under `mcp_server/src/mcp_server/tool_box/`:

   ```
   tool_box/
   └── my_feature/
       ├── __init__.py
       ├── tools.py          # add_tool(mcp) function
       ├── schemas.py        # Pydantic input/output models
       ├── tool_names.py     # ToolNames constants
       └── docstrings/
           ├── __init__.py   # DOCSTRINGS registry
           └── my_tool_docs.py
   ```

2. **Use `_tools_template/tools.py` as your reference** — every architectural decision is annotated.

3. **Register your tool** in `tool_box/__init__.py`:

   ```python
   from .my_feature.tools import add_tool as add_my_feature_tool

   def register_all_tools(mcp):
       add_template_tool(mcp)
       add_my_feature_tool(mcp)  # ← add here
   ```

4. **Add your tool name** to the root `ToolNames` registry in `tool_box/tool_names.py`.

---

## How to Write Effective Tool Docstrings

See `docs/TOOLS_BEST_PRACTICES.md` for the full guide. Key principles:

- **Everything is a prompt** — function names, argument names, docstrings, and responses all shape agent behavior.
- **Examples are contracts** — show the agent what success looks like; it will follow the pattern.
- **Flat arguments > nested** — agents struggle with deeply nested inputs; prefer flat Pydantic models.
- **ResponseFormat enum** — give agents control over output verbosity to manage token budgets.
- **Token budget** — allocate a max token budget per tool before you write it.

---

## How to Write Agent Instructions

See `docs/MCP_INSTRUCTIONS_FRAMEWORK.md` for the 4-layer framework:

1. **Mental Model** — domain-specific interpretive lens
2. **Categories** — mutually exclusive use-case classification slots
3. **Procedural Knowledge** — tool chains and guard rails per category
4. **Examples** — few-shot intent → action demonstrations

Edit `mcp_server/src/mcp_server/instructions/instructions.py` to replace the generic template with your domain instructions.

---

## VS Code Debugging

Add to `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "MCP Server",
            "type": "python",
            "request": "launch",
            "module": "mcp_server",
            "justMyCode": false,
            "env": {
                "PYTHONPATH": "${workspaceFolder}/mcp_server/src:${workspaceFolder}/packages/mcp_shared/src"
            }
        }
    ]
}
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/TOOLS_BEST_PRACTICES.md](docs/TOOLS_BEST_PRACTICES.md) | Best practices for designing MCP tools |
| [docs/MCP_INSTRUCTIONS_FRAMEWORK.md](docs/MCP_INSTRUCTIONS_FRAMEWORK.md) | 4-layer agent instructions design framework |
| [docs/WORKSPACES.md](docs/WORKSPACES.md) | UV workspace mechanics and package management |
| [docs/PACKAGES.md](docs/PACKAGES.md) | Creating and consuming workspace packages |
| [docs/PYTHON.md](docs/PYTHON.md) | Python and UV external resources |
