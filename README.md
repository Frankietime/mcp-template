# MCP Server Template

A generic, production-ready scaffold for building [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers with Python and [FastMCP](https://github.com/jlowin/fastmcp).

This template preserves the architecture, patterns, and best practices of a real production MCP server — stripped of all domain-specific code so you can fork it and build your own.

It also serves as an **onboarding project** and a **reference codebase for coding agents** (e.g. Claude, Cursor, Copilot). The structure, inline annotations, and documentation are intentionally designed so that an AI agent can read the codebase, understand the conventions, and rapidly scaffold new tools, workflows, and packages without human hand-holding.

---

## Architecture

```
mcp-template/
├── packages/
│   ├── equator/            # Prompt-toolkit TUI foundation — base layer for all terminal UIs
│   ├── beetle/             # Live log interpreter — ingests logs, explains them with a local LLM
│   ├── tropical/           # MCP protocol inspector — browse tools, resources, and prompts
│   ├── lab_mouse/          # Pydantic-AI agent REPL — tests whether the LLM uses your tools correctly
│   └── mcp_shared/         # Shared utilities (response builders, schemas, logging)
├── mcp_server/             # Main MCP Server
│   └── src/mcp_server/
│       ├── __main__.py          # Server entry point
│       ├── instructions/        # Agent instructions (4-layer framework)
│       ├── tool_box/            # Tool registration + _tools_template reference
│       └── workflows/           # Multi-step workflow orchestration
├── tests/
│   ├── unit/               # Unit tests for packages
│   └── agentic/            # Agentic integration tests (requires running server)
├── start.py                # One-command startup: mcp_server + lab_mouse
└── docs/                   # Architecture and best practices documentation
```

### Key Design Decisions

- **`mcp_shared`** — All tools use shared response builders (`SummaryResponse`, `ErrorResponse`) and `ResponseFormat` enum to control output verbosity and token usage.
- **`_tools_template`** — A fully annotated reference implementation. Every architectural decision is documented inline. Read this before creating your first tool.
- **Docstring Registry** — Tool descriptions are versioned separately from logic, enabling A/B testing and prompt engineering without touching business logic.
- **ToolNames Registry** — All tool names are constants. No inline strings — prevents typos and enables safe IDE refactors.

---

## Quickstart

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- [Ollama](https://ollama.com) — for local LLM inference (lab_mouse + beetle)

### 1. Install

```bash
git clone <your-repo-url> mcp-template
cd mcp-template
uv sync --all-packages
```

### 2. Pull Ollama models

Both **lab_mouse** and **beetle** use local models via Ollama running at `http://localhost:11434` (standard Ollama port — no configuration needed if Ollama is installed normally).

| Agent | Purpose | Default model | Recommended |
|---|---|---|---|
| **lab_mouse** | Agent REPL — calls MCP tools, reasons over results | `phi4-mini:3.8b` | `qwen3:4b` |
| **beetle** | Log interpreter — narrates live log output | `phi4-mini:3.8b` | `phi4-mini:3.8b` |

```bash
# Minimum — default model for both agents
ollama pull phi4-mini:3.8b

# Recommended — better reasoning for lab_mouse
ollama pull qwen3:4b

# Low-memory alternative
ollama pull qwen3:1.7b
```

Set the model for each agent in `.env` (or as environment variables):

```bash
AGENT_MODEL=ollama:qwen3:4b      # lab_mouse (default: ollama:phi4-mini:3.8b)
BEETLE_MODEL=ollama:phi4-mini:3.8b  # beetle    (default: ollama:phi4-mini:3.8b)

# Only needed if Ollama is NOT on the default port (11434)
# OLLAMA_BASE_URL=http://localhost:11434
```

> **Using Claude or OpenAI instead?** Set `AGENT_MODEL=claude-sonnet-4-6` (or any pydantic-ai model string) and add `ANTHROPIC_API_KEY` to `.env`. No Ollama required for lab_mouse in that case.

### 3. Configure environment

```bash
cp .env.sample .env
# Edit .env — at minimum set AGENT_MODEL if not using the default
```

### 4. Start everything

**One command** — starts mcp_server in a new terminal, waits for it to be ready, then launches lab_mouse:

```bash
uv run python start.py
```

Or start them separately:

```bash
# Terminal 1
uv run mcp_server

# Terminal 2 (once the server is ready)
uv run lab_mouse
```

Health check:

```bash
curl http://127.0.0.1:8000/healthcheck
# → OK
```

### 5. Use beetle (optional)

From inside lab_mouse, type `/beetle` to open beetle in a new terminal, pre-loaded with current logs and wired for live forwarding.

---

## equator TUI guide

All terminal apps — **lab_mouse** and **beetle** — share the same TUI built on **equator**.

### Layout

```
┌──────────────────────── lab_mouse ─────────────────────────┐
│                                                             │
│  Conversation history                                       │
│                                                             │
│  ▏ ((o))  what sections does the resume have?              │
│                                                             │
│  ▏ ))o((  ⚙ md_list_sections(document="RESUME")…          │
│  ▏ ))o((  ⚙ md_list_sections… ✓ 8 sections found          │
│  ▏ ))o((  I found 8 sections: Summary, Experience, …      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  AGENT · 312 chars                                          │
│  Preview: I found 8 sections: Summary, Experience, …       │
│  Tools: 1/1 completed    F2 inspect                        │
├─────────────────────────────────────────────────────────────┤
│  [INF] httpx: POST /mcp 200                                 │
│  [DBG] mcp: tool result received                            │
├─────────────────────────────────────────────────────────────┤
│  > type here                                                │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  ollama:qwen3:4b | MCP: ✓ | ●DBG ●INF ●WRN ●ERR ●CRT      │
│  Context  ████░░░░░░░░░░░░░░░░░░  4,200 / 32,768  (13%)    │
│                          TAB = toggle help                  │
└─────────────────────────────────────────────────────────────┘
```

**Visual identity:**

| Symbol | Meaning |
|---|---|
| `((o))` | You (the user) |
| `))o((` | The agent |
| `=){` | beetle |

### Key bindings

| Key | Action |
|---|---|
| `Enter` | Send message |
| `Esc+Enter` | Insert newline |
| `↑ / ↓` | Navigate conversation history (when input is empty) |
| `↑ / ↓` | Scroll inspector content (when in expanded inspect mode) |
| `Esc` | Clear message cursor (return to auto-follow) |
| `Ctrl+O` | Toggle logs panel |
| `Shift+Tab` | Toggle internal logs panel |
| `← / →` | Page through logs (when logs panel is open) |
| `← / →` | Cycle tool calls (when a message is selected) |
| `F2` | Toggle inspect / detail expansion |
| `Tab` | Toggle help sidebar |
| `↑ / ↓` | Navigate model selector (when open) |
| `Enter` | Confirm model selection |
| `Esc` | Cancel model selector |
| `Ctrl+X` | Quit |

### Slash commands

Type any `/command` in the input. Tab-completion is available.

**Universal (lab_mouse + beetle):**

| Command | Description |
|---|---|
| `/help` | Show key bindings and all commands in the logs panel |
| `/logs` | Show current active log levels |
| `/logs err crt` | Show only ERR and CRT |
| `/logs all` | Enable all five levels (default on startup) |
| `/logs none` | Silence all levels |
| `/clear` | Clear the conversation history |
| `/clearlogs` | Clear the logs panel |
| `/q` | Quit |

**lab_mouse only:**

| Command | Description |
|---|---|
| `/beetle` | Launch beetle in a new terminal with live log forwarding |
| `/tropical` | Open tropical inspector, auto-connected to the active MCP server |
| `/tropical <url>` | Open tropical connected to a specific URL |
| `/tools` | List tools from connected MCP servers |
| `/model <name>` | Switch model inline — e.g. `/model ollama:qwen3:4b` |

### Log levels

The status bar shows which levels are active (filled dot = on, empty = off). All levels are on by default.

```
●DBG  ●INF  ●WRN  ●ERR  ●CRT
```

### Inspect mode (F2)

When a message is selected (`↑ / ↓`):
- **Compact**: one summary line shown below the message — role, timing, tool count.
- **Expanded** (press `F2`): full tool args + results with JSON syntax highlighting.
  - `← / →` cycles through tool calls within the same turn.
  - `↑ / ↓` scrolls through long inspector content.
  - `F2` again collapses; `Esc` clears the selection entirely.

---

## Developer Toolchain

### equator — TUI foundation

The shared prompt-toolkit base that `beetle` and `lab_mouse` are built on. Not a standalone tool — a library. Use it directly if you want to wrap your own pydantic-ai agent in a full terminal interface:

```python
import equator
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

agent = Agent("openai:gpt-4o", toolsets=[MCPServerStreamableHTTP("http://localhost:8000/mcp")])
equator.run(agent, name="my-tester")
```

The lower layers (`protocol.py`, `state.py`, `components/`) have no pydantic-ai dependency — any async backend that implements `SessionProtocol` can drive the TUI. `beetle` uses this to run a completely different session type with the same rendering infrastructure.

Custom commands are registered via `CommandRegistry` and passed to `equator.run()`. Three kinds: `ACTION` (executes TUI-side logic), `PROMPT` (pre-fills the input box), `SCRIPT` (sends a fixed message to the agent).

See [`packages/equator/README.md`](packages/equator/README.md) for the full reference.

### beetle — live log interpreter

Wraps any Python process with a full-screen TUI that ingests logs over TCP and interprets them in plain language using a local LLM. No API keys required — runs on [Ollama](https://ollama.com).

```bash
uv run beetle   # listens on localhost:9020
```

Wire your application with the built-in handler:

```python
from beetle.log_server import BeetleHandler
import logging
logging.getLogger().addHandler(BeetleHandler())
```

Or use the zero-dependency snippet if you don't want `beetle` as a project dependency:

```python
import json, socket, logging

class BeetleHandler(logging.Handler):
    def __init__(self, host="localhost", port=9020):
        super().__init__()
        self._sock = socket.create_connection((host, port))

    def emit(self, record):
        import traceback
        exc = traceback.format_exc() if record.exc_info else None
        data = json.dumps({
            "level": record.levelno, "name": record.name,
            "msg": record.getMessage(), "exc": exc,
        }) + "\n"
        try:
            self._sock.sendall(data.encode())
        except OSError:
            self.handleError(record)

logging.getLogger().addHandler(BeetleHandler())
```

Options:

```bash
beetle --port 9021          # custom port (default: 9020)
beetle --logs ./app.log     # pre-load a log file on startup
beetle --no-server          # disable TCP listener (static analysis)
cat app.log | beetle        # pipe mode

BEETLE_MODEL=ollama:phi4-mini:3.8b   # interpreter model (default: ollama:phi4-mini:3.8b)
```

See [`packages/beetle/README.md`](packages/beetle/README.md) for the full reference.

### tropical — MCP protocol inspector

A full-screen TUI for raw MCP protocol inspection. Browse tools, resources, and prompts; execute requests; view responses with syntax highlighting and markdown rendering. No API keys required.

```bash
uv run tropical                                                           # standalone
uv run tropical connect-http http://localhost:8000/mcp                    # connect directly
uv run tropical connect-http http://localhost:8000/mcp --header "Authorization=Bearer <token>"
```

Supports STDIO, HTTP (Streamable), and TCP transports. Server configs persist in `~/.config/tropical/servers.yaml`.

### lab_mouse — agent REPL

An interactive terminal agent connected to your MCP server. Tests whether the LLM actually uses your tools correctly — not just whether the tools return the right data.

```bash
uv run python start.py      # starts both mcp_server and lab_mouse
```

or manually:

```bash
uv run mcp_server           # Terminal 1
uv run lab_mouse            # Terminal 2
```

---

## Running Tests

```bash
uv run pytest
```

Agentic tests require a running server:

```bash
# Terminal 1: start the server
uv run mcp_server

# Terminal 2: run agentic tests
uv run pytest tests/agentic/ -v
```

Coverage threshold: 80% (enforced in CI).

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
| [packages/equator/README.md](packages/equator/README.md) | equator full reference |
| [packages/beetle/README.md](packages/beetle/README.md) | beetle full reference |
