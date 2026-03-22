# equator

> A plug-and-play pydantic-ai agent TUI for MCP server development.

equator puts a full interactive terminal harness around any `pydantic_ai.Agent`. When you are building an MCP server, you need two things running side-by-side: a protocol inspector for the raw JSON-RPC layer, and a real agent to test whether the LLM actually uses your tools correctly. equator is the second one.

```python
import equator
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

agent = Agent("openai:gpt-4o", toolsets=[MCPServerStreamableHTTP("http://localhost:8000/mcp")])
equator.run(agent)
```

That's it. You get streaming responses, live tool call visibility with args and results, log monitoring, model hot-swap, and a slash-command system you can extend with your own test scenarios.

---

## Why equator

When iterating on an MCP server you need two complementary tools:

| Concern | Tool |
|---|---|
| Does the tool return the right data? | MCP Inspector / mcp-probe / f/mcptools |
| Does the agent use the tool correctly? | **equator** |
| Does the full chain reason well? | **equator** |
| Custom `/test-my-scenario` scripts | **equator** |

pydantic-ai's built-in CLI (`clai`) is a plain readline REPL — no tool call visibility, no streaming display, no command system. equator fills that gap without requiring you to write a TUI from scratch.

### vs other tools

| Tool | Language | Wraps any pydantic-ai Agent? | Terminal-native? | Custom commands? |
|---|---|---|---|---|
| **equator** | Python | Yes — zero adapter | Yes | Yes |
| aichat | Rust | No — HTTP endpoint only | Yes | No |
| mcp-client-for-ollama | Python | No — Ollama only | Yes (Textual) | No |
| Toad | Python | No — requires ACP protocol | Yes (Textual) | No |
| clai (pydantic-ai) | Python | Yes | Readline only | No |

---

## Installation

equator lives inside the `mcp-template` workspace. No separate install needed:

```bash
uv run equator          # once the CLI entry point is wired
```

Or use it as a library from any workspace package:

```python
import equator
equator.run(my_agent)
```

---

## Quick start

### Minimal

```python
import equator
from pydantic_ai import Agent

agent = Agent("openai:gpt-4o", system_prompt="You are a helpful assistant.")
equator.run(agent)
```

### With MCP server

```python
import equator
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

agent = Agent(
    "openai:gpt-4o",
    toolsets=[MCPServerStreamableHTTP("http://localhost:8000/mcp")],
    system_prompt="You have access to MCP tools. Use them.",
)
equator.run(agent, name="my-mcp-tester")
```

### With model switcher and custom commands

```python
import equator
from equator.commands import CommandRegistry

cmds = equator.base_registry().extend()

@cmds.register("ping", "Call the ping tool and show the result")
def _ping(args, state, app):
    state.internal_log_lines.append("[INF] ping: sending /ping to agent…")
    state.active_panel = "internal_logs"
    app._send_message("/ping")
    app.invalidate()

equator.run(
    agent,
    name="my-mcp-tester",
    available_models=["openai:gpt-4o", "openai:gpt-4o-mini", "ollama:qwen3:4b"],
    commands=cmds,
)
```

---

## TUI layout

```
┌───────────────────────── my-mcp-tester ──────────────────────────┐
│                                                                   │
│  Conversation history                                             │
│                                                                   │
│  ▏ what tools do you have?                                        │
│                                                                   │
│  ▏ ⚙ list_tools(filter="*")…                                     │
│  ▏ ⚙ list_tools… ✓ "search, fetch, summarise"                    │
│  ▏ I have access to three tools: search, fetch, and summarise.   │
│                                                                   │
├───────────────────────────────────────────────────────────────────┤
│  [INF] mcp: connected to http://localhost:8000/mcp               │
│  [DBG] httpx: POST /mcp 200                                       │
├───────────────────────────────────────────────────────────────────┤
│  > type here                                                      │
│                                                                   │
├───────────────────────────────────────────────────────────────────┤
│  openai:gpt-4o | MCP: ✓ | ●DBG ○INF ○WRN ●ERR ○CRT             │
│  Context  ████░░░░░░░░░░░░░░░░░░  4,200 / 32,768  (13%)          │
└───────────────────────────────────────────────────────────────────┘
```

---

## Key bindings

| Key | Action |
|---|---|
| `Enter` | Send message |
| `Esc+Enter` | Insert newline |
| `↑ / ↓` | Scroll conversation history |
| `Tab` | Toggle raw logs panel |
| `Shift+Tab` | Toggle internal logs panel |
| `← / →` | Page through logs (when logs panel open) |
| `↑ / ↓` | Navigate model selector (when open) |
| `Enter` | Confirm model selection |
| `Ctrl+L` | Clear conversation |
| `Ctrl+X` | Quit |

---

## Commands

Type any `/command` in the input. Tab-completion is available.

| Command | Description |
|---|---|
| `/help` | Show key bindings and all commands |
| `/tools` | List tools discovered from connected MCP servers |
| `/model <name>` | Switch model inline — e.g. `/model openai:gpt-4o-mini` |
| `/logs` | Show active log levels |
| `/logs err crt` | Show only ERR and CRT |
| `/logs all` | Enable all levels |
| `/logs none` | Silence all levels |
| `/q` | Quit |

Custom commands are registered via `CommandRegistry` and passed to `equator.run()`. Three kinds:

| Kind | Behaviour |
|---|---|
| `ACTION` | Executes TUI-side logic immediately |
| `PROMPT` | Pre-fills the input box for the user to edit then send |
| `SCRIPT` | Sends a fixed message to the agent without user editing |

---

## Architecture

equator is a layered foundation. The lower layers have no pydantic-ai dependency — only `prompt_toolkit`. This lets `beetle` and any future non-pydantic consumer use the same TUI primitives.

```
equator/protocol.py        ← SessionEvent union + SessionProtocol (zero deps)
equator/state.py           ← TuiState shared render state (zero deps)
equator/commands.py        ← CommandRegistry + SlashCompleter (prompt-toolkit)
equator/components/        ← HistoryControl, InputControl, StatusControl, … (prompt-toolkit)
equator/app.py             ← BaseTuiApp — wires everything, owns async loops (prompt-toolkit)
──────────────────────── pydantic-ai boundary ────────────────────────────────────
equator/log_handler.py     ← routes Python logging into TuiState
equator/stream_handler.py  ← maps pydantic-ai stream events → SessionEvents
equator/session.py         ← PydanticAISession wraps any Agent[Any, str]
equator/mcp_commands.py    ← /tools and /model built-in commands
equator/equator_app.py     ← EquatorApp(BaseTuiApp) — batteries-included
equator/__init__.py        ← public API: equator.run(agent, …)
```

### SessionProtocol

Any object that implements `subscribe` and `clear` can drive the TUI — not just pydantic-ai agents. `beetle` uses its own `BeetleSession`; `lab_mouse` uses `AgentSession`. `equator.run()` uses `PydanticAISession`.

```python
class SessionProtocol(Protocol):
    def subscribe(self, listener: Callable[[SessionEvent], None]) -> Callable[[], None]: ...
    def clear(self) -> None: ...
```

### SessionEvent union

```
TextDeltaEvent      — streaming text chunk
ToolCallEvent       — tool dispatched (name + args)
ToolResultEvent     — tool completed (output)
AgentStartEvent     — agent began processing
AgentEndEvent       — agent finished (final output)
TokenUsageEvent     — updated token count
ClearedEvent        — conversation cleared
```

### Extension points

**Custom session backend** — implement `SessionProtocol` and pass it to `BaseTuiApp` directly. The TUI knows nothing about pydantic-ai; any async backend works.

**Custom commands** — build a `CommandRegistry`, register handlers, pass via `equator.run(..., commands=my_registry)`. Commands receive `(args, state, app)` — full access to render state and the app's public methods.

**Custom style** — subclass `EquatorApp`, override `_STYLE`, call `super().__init__()`.

---

## Visual identity

| Symbol | Meaning |
|---|---|
| `((o))` | You (the user) |
| `))o((` | The agent |

The loader animation morphs between `((o))` and `))o((` while the agent thinks.

---

## Roadmap

- [x] `BaseTuiApp` — prompt_toolkit foundation, layout, key bindings, async loops
- [x] `SessionProtocol` — typed event bus separating session from render
- [x] `CommandRegistry` — slash-command system with ACTION / PROMPT / SCRIPT kinds
- [x] Components — history, input, status bar, context bar, log panels, model selector
- [ ] `PydanticAISession` — generic pydantic-ai agent wrapper
- [ ] `EquatorApp` — batteries-included subclass with MCP lifecycle
- [ ] `equator.run()` — one-line entry point
- [ ] `/tools` — list discovered MCP tools
- [ ] `/model <name>` — inline model switch
- [ ] Tool call args + result display in history
- [ ] `equator` CLI entry point
