# beetle `=){`

---

## What beetle is

beetle is a logging-first developer tool for quickly iterating AI projects.

It wraps any agent or MCP server with a full-screen terminal UI that keeps logs, agent interactions, and debugging tools in one place — so the developer never has to leave the terminal to understand what their system is doing.

The core of beetle is the logging layer: capturing, classifying, and interpreting what the system emits in real time. Everything else — the agent conversation, the plugin testing tools, the session recording — is built on top of that foundation.

beetle is designed for the moment between "something feels wrong" and "I know what to fix." It shortens that moment.

---

## What's been built

### TUI (terminal user interface)

A full-screen terminal UI built on `prompt_toolkit`. This is beetle's current form — it wraps a pydantic-ai agent connected to an MCP server, giving the developer a single terminal surface for chatting with the agent, reading live logs, and invoking beetle for log interpretation.

**Visual identity:**
- `((o))` — the user (overridable via `TUI_UNAME`)
- `))o((` — the agent
- `=){` — beetle
- Loader animation morphs between `((o))` and `))o((` while the agent thinks

**Architecture:**
- Two queues decouple commands from agent messages: `_cmd_queue` (always responsive) and `_msg_queue` (serialised agent runs)
- `TuiState` is the single source of truth — components are pure render functions, only `TuiApp` mutates state
- Comma-command registry (`,<name>`) — every TUI feature is reachable via command

**Components built:**
- `history` — conversation between user and agent
- `logs` — live log panel, toggleable, with its own input buffer for beetle mode
- `input` — main user input
- `status` — spinner + model info
- `context_bar` — token usage

**Built-in commands:**
- `,1` — toggle log panel
- `,2` — verbose (DEBUG) logs + activate beetle
- `,0` — swap theme (dark ↔ light)
- `,print` — export conversation to timestamped `.md` file
- `,3` — list available commands
- `,4` / `,beetle` — activate beetle mode

**Beetle mode:**
- Activated via `,beetle`, `,4`, or the `F4` key binding
- Focuses the log panel input and asks: `What are you looking for? =){`
- User's answer is the "intention" — beetle reads the current log buffer through that lens
- Response is appended to the log panel as `[BTL] ...`
- beetle is a separate pydantic-ai agent with no tools — LLM + log context only, 3–5 sentences max

**Themes:** dark / light

---

## Integration

beetle is a package. Dropping it into any Python project activates log capture, session recording, and the TUI. No instrumentation, no schema changes — attach to whatever is already running.

### Three integration layers

**Layer 1 — Universal (stdlib logging)**
Captures anything that logs through Python's `logging` module. Works with any framework.
```python
import beetle
async with beetle.session():
    await my_server.run()
```
Attaches `BeetleLogHandler` to the roots: `mcp`, `fastmcp`, `httpx`, and the user's own loggers. This is the baseline — always on, zero config.

**Layer 2 — pydantic-ai (event stream)**
pydantic-ai has no stdlib logging at all. Its signals come from two sources:
- `Agent.instrument_all()` — emits OpenTelemetry spans for agent runs, tool calls, token usage
- `event_stream_handler` — typed event stream: `FunctionToolCallEvent`, `FunctionToolResultEvent`, `AgentRunResultEvent`, streaming deltas

beetle provides a `BeetleEventHandler` that plugs into `event_stream_handler` and records tool calls, results, and usage into the session.

```python
from beetle.adapters.pydantic_ai import BeetleEventHandler

result = await agent.run_stream(
    prompt,
    event_stream_handler=BeetleEventHandler(),
)
```

**Layer 3 — FastMCP (middleware)**
FastMCP has a `Middleware` base class with specific hooks: `on_call_tool`, `on_message`, `on_initialize`, `on_read_resource`. beetle provides a `BeetleMiddleware` that captures every tool call with timing and routes it into the session.

```python
from beetle.adapters.fastmcp import BeetleMiddleware

mcp = FastMCP("my-server")
mcp.add_middleware(BeetleMiddleware())
```

### What each layer captures

| Source | Signal | Recorded as |
|---|---|---|
| `mcp.*` loggers | Transport events, protocol errors, session lifecycle | `session.jsonl` |
| `fastmcp.*` loggers | Server internals, auth events, server errors | `session.jsonl` |
| `httpx` logger | HTTP requests/responses to model provider | `session.jsonl` |
| pydantic-ai event stream | Tool calls + results, agent run start/end, token usage | `session.jsonl` + `plugins/pydantic_ai/` |
| FastMCP middleware | Tool calls + timing, all MCP protocol traffic | `session.jsonl` + `plugins/fastmcp/` |

### Package structure

```
beetle/
├── __init__.py               # public API: session(), attach(), BeetleSession
├── session.py                # session context manager: opens folder, manages writers
├── handler.py                # BeetleLogHandler — stdlib logging, TUI-agnostic
├── writer.py                 # append-only JSONL + index writers
├── event_detector.py         # pattern-based severity classifier, breadcrumb buffer
├── exporter.py               # ,share / ,sessions — summary block + full artifact
└── adapters/
    ├── pydantic_ai.py        # BeetleEventHandler (event_stream_handler compatible)
    └── fastmcp.py            # BeetleMiddleware (Middleware subclass)
```

### Relationship to the TUI

The TUI's current `TuiLogHandler` writes directly into `state.log_lines`. After extraction, `BeetleLogHandler` writes to the session — and the TUI becomes a consumer of the session, not the primary writer.

```
log source → BeetleLogHandler → session.jsonl
                                      ↓
                              TUI log panel (reads session, displays lines)
                              event detector (pattern-matches on write)
                              beetle agent (reads buffer on demand)
```

The TUI does not own the log data. beetle's session does. The TUI is one of several surfaces that can read from it.

---

## Roadmap

### Next: MCP Inspector plugin

The MCP Inspector is a plugin/extension installable into beetle.

Plugins and extensions are testing applications wrapped by a very small model — run with minimum reasoning, just enough to trigger the plugin functionality through commands and other TUI features.

The idea: provide intelligent UI for testing tools that makes the debugging and developer testing process intuitive, fast, and ergonomic.

**MCP Inspector specifically:** lets developers test MCP server tools directly from the terminal — list tools, call them with arguments, inspect schemas — without leaving the TUI or opening a browser.

### Logging system

When beetle is activated, it turns on not only the agent and the extensions but also a logging system. This system:

- Records information from the debugging process to folders
- Logs are recorded in one place, divided by different categories
- Can be automatically extracted for certain events
- Can be extracted with commands to be comfortably shared

---

## Models

beetle uses two distinct model roles. They are separate concerns with different requirements.

### beetle agent — log interpreter

Reads 50–200 log lines, produces 3–5 sentence plain-language interpretation. Needs reading comprehension and language quality. Does not need reasoning, tool use, or code generation.

| Preference | Model | Ollama tag | Params | Quant |
|---|---|---|---|---|
| Default | Qwen3 | `qwen3:4b` | 4B | Q4_K_M |
| Best prose | Phi-4-mini | `phi4-mini` | 3.8B | Q4_K_M |
| Low memory | Qwen3 | `qwen3:1.7b` | 1.7B | Q4_K_M |

Use `/no_think` in the system prompt (or `think: false` in the Ollama API call) to disable chain-of-thought. beetle is not reasoning — it is translating. CoT adds latency and verbosity with no benefit here.

Escalate from Q4_K_M to Q8_0 only if summaries are garbled or noticeably degraded. Language quality matters for this role.

### Plugin dispatcher — command router

Maps a short natural language string to one of ~5 predefined commands. This is classification, not generation. The model does not need to reason or produce prose.

| Preference | Model | Ollama tag | Params | Quant |
|---|---|---|---|---|
| Default | Qwen3 | `qwen3:0.6b` | 0.6B | Q4_K_M |
| Higher accuracy | Qwen3 | `qwen3:1.7b` | 1.7B | Q4_K_M |
| Alternative | SmolLM2 | `smollm2:1.7b` | 1.7B | Q4_K_M |

Use Ollama's `format` field to constrain output to a valid enum of command names:
```json
{ "format": { "type": "string", "enum": ["list_tools", "call_tool", "show_schema"] } }
```
This makes even a 0.6B model a reliable dispatcher regardless of input phrasing. The model is not generating — it is classifying into a forced choice.

### Deployment requirements

- **Same model family across both roles.** Qwen3 for both beetle (4B) and dispatchers (0.6B) means one family, consistent behavior, shared Ollama pull.
- **Keep dispatcher models resident.** Cold-start latency is the enemy of sub-second dispatch. Set `OLLAMA_KEEP_ALIVE=-1` so the 0.6B stays loaded in memory between requests. beetle agent (4B) can load on demand.
- **Q4_K_M everywhere by default.** ~95% quality retained, ~4x smaller than FP16. Start here, escalate only if needed.

---

## Skills (design intent)

beetle will have pluggable debugging / logging / problem solving skills.

Skills are domain-specific capabilities beetle can invoke — separate from plugins, which are UI testing tools. Where a plugin is a testing interface, a skill is a reasoning module: something beetle knows how to *do*.

Examples of what skills might cover: interpreting a specific log format, finding root causes of a recurring error pattern, summarizing a session's problems, comparing logs against a baseline, generating fix suggestions.

Skills are pluggable — installable independently, composable, and invoked by beetle autonomously when relevant. Explicit command triggering is planned but not the initial target.

---

## Plugin system (design intent)

Plugins / extensions are:
- Self-contained testing applications
- Wrapped by a very small model (minimum reasoning — just to dispatch commands)
- Reachable via commands and TUI features
- The intelligence is in the UI ergonomics, not the model depth

MCP Inspector is the first first-party plugin.
