# beetle `=){`

> A logging-first developer tool for quickly iterating AI projects.

beetle wraps any Python application with a full-screen terminal UI that keeps live logs, agent interactions, and log interpretation in one place — so you never have to leave the terminal to understand what your system is doing.

The core of beetle is the logging layer: capturing, classifying, and interpreting what the system emits in real time. Everything else is built on top of that foundation.

beetle is designed for the moment between *"something feels wrong"* and *"I know what to fix."* It shortens that moment.

---

## Installation

Install beetle into your developer environment (not necessarily your project's production environment):

```bash
# pip
pip install beetle

# uv (recommended)
uv add beetle --dev
```

beetle requires Python 3.13+.

> **Workspace / monorepo?** If you're working inside the `mcp-template` workspace, beetle is already a local package. Start it with `uv run beetle` directly — no separate install needed.

---

## Quickstart

### 1. Start beetle

```bash
uv run beetle
# or
python -m beetle
```

beetle opens a full-screen TUI and starts listening for logs on `localhost:9020`.

### 2. Wire your project's logger

**Option A — use the built-in handler** (requires `beetle` installed as a dependency of your project, e.g. `uv add beetle`):

```python
import logging
from beetle.log_server import BeetleHandler

logging.getLogger().addHandler(BeetleHandler())
```

**Option B — zero-dependency snippet** (copy-paste, no imports required):

```python
import json, socket, logging, traceback

class BeetleHandler(logging.Handler):
    def __init__(self, host="localhost", port=9020):
        super().__init__()
        self._sock = socket.create_connection((host, port))

    def emit(self, record):
        exc = traceback.format_exc() if record.exc_info else None
        data = json.dumps({
            "level": record.levelno,
            "name": record.name,
            "msg": record.getMessage(),
            "exc": exc,
        }) + "\n"
        try:
            self._sock.sendall(data.encode())
        except OSError:
            self.handleError(record)

logging.getLogger().addHandler(BeetleHandler())
```

### 3. Run your project

Logs stream into beetle in real time. Ask beetle to interpret them — just type in the TUI.

### Options

```bash
beetle --port 9021          # custom port (default: 9020)
beetle --logs ./app.log     # load a static log file on startup
beetle --no-server          # disable TCP listener (for static analysis)
cat app.log | beetle        # pipe mode — reads stdin
```

### Environment

```bash
BEETLE_MODEL=ollama:qwen3:4b   # log interpreter model (default: ollama:phi4-mini:3.8b)
BEETLE_PORT=9020               # TCP port for log ingestion
```

---

## TUI guide

```
┌─────────────────────── beetle =){ ───────────────────────┐
│                                                           │
│  Interpretation panel  (beetle's responses)              │
│                                                           │
├───────────────────────────────────────────────────────────┤
│  Raw logs panel  (live incoming logs)                     │
│  [DBG] httpx: GET /api/tools 200                         │
│  [ERR] mcp: connection refused on port 8080              │
├───────────────────────────────────────────────────────────┤
│  > type here                                              │
├───────────────────────────────────────────────────────────┤
│  model | MCP: ✓ | ●DBG ○INF ○WRN ●ERR ○CRT              │
│  Context  ████░░░░░░░░░░░░░░░░░░  12,400 / 32,768        │
└───────────────────────────────────────────────────────────┘
```

### Navigation

| Key | Action |
|---|---|
| `Tab` | Show raw logs panel |
| `Shift+Tab` | Show interpretation panel |
| `Ctrl+P` | Toggle log panel overlay |
| `Enter` | Send message to beetle |
| `Esc+Enter` | Insert newline |
| `Ctrl+L` | Clear conversation |
| `Ctrl+X` | Quit |

### Commands

Type any `/command` in the input box. Tab-completion is available.

| Command | Description |
|---|---|
| `/help` | Show this reference |
| `/logs` | Show current active log levels |
| `/logs err crt` | Show only ERR and CRT levels |
| `/logs all` | Enable all levels |
| `/logs none` | Disable all levels |
| `/1` | Toggle log panel |
| `/q` | Quit |

### Log levels

The status bar shows which levels are active (filled dot = on, empty = off).

```
●DBG  ○INF  ○WRN  ●ERR  ○CRT
```

Control with `/logs`:
```
/logs dbg err      → only DBG and ERR
/logs all          → all five levels
/logs none         → silence everything
/logs inf wrn err  → INFO, WARNING, ERROR
```

### Asking beetle

beetle interprets your logs through the lens of whatever you're looking for.

```
> what caused the 401?
> is the MCP handshake completing?
> why is the agent retrying?
```

Responses use a flow chain format:

```
*agent started* > *tool called* > *POST /api/submit* > *401 unauthorized* > *token missing from header*
```

Key terms are **bold** — scan the chain left to right for the narrative, then bold terms for the specifics.

---

## Architecture

beetle is a standalone process that receives logs over TCP and interprets them with a local LLM.

```
your app
  └─ BeetleHandler ──TCP──► beetle TUI
                               ├─ raw logs panel  (real-time display)
                               ├─ interpreter     (pydantic-ai agent + local LLM)
                               └─ conversation    (your questions + beetle's answers)
```

### TUI layers

| Layer | Responsibility |
|---|---|
| `BaseTuiApp` | prompt_toolkit wiring, layout, key bindings, event loop |
| `BeetleTuiApp` | beetle-specific queue shape, debounced auto-analysis, log server lifecycle |
| `BeetleSession` | satisfies `SessionProtocol`, calls the agent, emits typed events |
| `beetle agent` | pydantic-ai Agent with no tools — LLM + log context only |

### Auto-analysis

When a burst of logs arrives and then goes quiet for 1.5 seconds, beetle automatically sends a brief narration (one sentence). This keeps the interpretation panel live without you having to ask.

---

## Models

beetle uses a local LLM via Ollama. No API keys required.

### Log interpreter

Reads 50–200 log lines, produces a plain-language chain. Needs reading comprehension and language quality — not reasoning or code generation.

| | Model | Ollama tag | Size |
|---|---|---|---|
| **Default** | Phi-4-mini | `phi4-mini:3.8b` | 3.8B Q4_K_M |
| Recommended | Qwen3 | `qwen3:4b` | 4B Q4_K_M |
| Low memory | Qwen3 | `qwen3:1.7b` | 1.7B Q4_K_M |

Use `/no_think` in the system prompt (already set) to disable chain-of-thought on Qwen3 — beetle is translating, not reasoning. CoT adds latency with no benefit here.

### Setup

```bash
# Install Ollama: https://ollama.com
ollama pull phi4-mini        # default
ollama pull qwen3:4b         # recommended

# Select model
export BEETLE_MODEL=ollama:qwen3:4b
uv run beetle
```

---

## Integration reference

### BeetleHandler protocol

Each log record is sent as a newline-delimited JSON object:

```json
{"level": 20, "name": "myapp.service", "msg": "connected", "exc": null}
```

`level` follows stdlib conventions: `10=DEBUG`, `20=INFO`, `30=WARNING`, `40=ERROR`, `50=CRITICAL`.

### Attaching to specific loggers

```python
import logging
from beetle.log_server import BeetleHandler

handler = BeetleHandler(host="localhost", port=9020)
handler.setLevel(logging.DEBUG)

# Attach to specific loggers
for name in ("httpx", "mcp", "myapp"):
    logging.getLogger(name).addHandler(handler)
```

### Pipe mode

```bash
tail -f /var/log/app.log | beetle --no-server
```

Reads lines from stdin and feeds them directly into the log buffer. Useful for tailing existing log files.

### Static file analysis

```bash
beetle --logs ./session.log --no-server
```

Loads a log file on startup — no TCP server, no live ingestion. Ask beetle questions about a past session.

---

## Roadmap

### Now

- [x] Full-screen TUI with split log / interpretation panels
- [x] TCP log server (port 9020, newline-delimited JSON)
- [x] Local LLM interpreter (Ollama, phi4-mini / qwen3)
- [x] Auto-analysis on log burst settle
- [x] `/logs` command for level filtering
- [x] Bold key terms in responses (`*term*`)
- [x] Pipe mode and static file analysis

### Next: MCP Inspector plugin

A first-party plugin that lets developers test MCP server tools directly from the terminal — list tools, call them with arguments, inspect schemas — without leaving the TUI or opening a browser.

Plugins are self-contained testing applications wrapped by a very small model (minimum reasoning — just enough to dispatch commands). The intelligence is in the UI ergonomics, not the model depth.

### Logging system

When beetle is activated, it turns on a structured logging system:

- Records the debugging process to session folders
- Logs divided by category (transport, agent, tool calls, errors)
- Automatic extraction on certain events
- Export commands for sharing sessions

### Skills

Pluggable reasoning modules beetle can invoke autonomously:

- Interpreting a specific log format
- Finding root causes of recurring error patterns
- Summarising a session's problems
- Comparing logs against a baseline
- Generating fix suggestions

Skills are domain-specific capabilities — separate from plugins (UI testing tools). Where a plugin is a testing interface, a skill is a reasoning module.

---

## Visual identity

| Symbol | Meaning |
|---|---|
| `((o))` | You (the user) |
| `))o((` | The agent |
| `=){` | beetle |

The loader animation morphs between `((o))` and `))o((` while the agent thinks.
