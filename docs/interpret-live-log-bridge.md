# Plan: `/interpret` Live Log Bridge

## Goal

When the user runs `/interpret` inside `lab_mouse`, beetle launches in a new terminal with the current log history pre-loaded **and** stays connected to receive all future logs in real time.

---

## What already exists

### `beetle --logs <file> --port <port>` — already supported

`beetle/__main__.py` already accepts both flags simultaneously:

```python
log_lines = args.logs.read_text().splitlines()   # pre-load history
session = BeetleSession(log_lines)
BeetleTuiApp(session, port=port).run()           # also starts TCP server
```

Beetle will pre-populate its log buffer from the file **and** listen on the port for live updates. No changes needed to beetle.

### `BeetleHandler` — already the right mechanism

`beetle/log_server.BeetleHandler` is a Python `logging.Handler` that connects to beetle's TCP server and forwards records as JSON. `lab_mouse/tui/log_handler.py` already imports and uses it when `BEETLE_PORT` env var is set:

```python
from beetle.log_server import BeetleHandler
beetle_handler = BeetleHandler(port=int(beetle_port))
```

This is the correct live-forwarding path. It must remain untouched.

### Current `/interpret` — static only

```python
# _launch_beetle() today:
tf.write("\n".join(self._state.log_lines))
subprocess.Popen(["wt", "--", "cmd", "/k", f'uv run beetle --logs "{tf.name}"'])
```

No `--port`, no `BeetleHandler` attached. Beetle gets a frozen snapshot and nothing more.

---

## What needs to change

Only `lab_mouse/tui/app.py` — specifically `_launch_beetle()` and its teardown.

### Revised `_launch_beetle()`

```python
def _launch_beetle(self) -> None:
    from beetle.log_server import DEFAULT_PORT

    # 1. Write snapshot (same as before — gives beetle immediate history)
    tf = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8")
    tf.write("\n".join(self._state.log_lines))
    tf.close()

    # 2. Launch with --logs (history) AND --port (live)
    cmd = f'uv run beetle --logs "{tf.name}" --port {DEFAULT_PORT}'
    try:
        subprocess.Popen(["wt", "--", "cmd", "/k", cmd])
    except FileNotFoundError:
        subprocess.Popen(f"start cmd /k {cmd}", shell=True)  # noqa: S602

    # 3. Attach BeetleHandler once beetle's TCP server is ready
    asyncio.create_task(self._attach_beetle_handler(DEFAULT_PORT))
```

### New coroutine `_attach_beetle_handler()`

`BeetleHandler.__init__` calls `socket.create_connection` synchronously — it fails immediately if beetle isn't listening yet. We retry until beetle's server is up (~1 s boot time).

```python
async def _attach_beetle_handler(self, port: int) -> None:
    import logging
    from beetle.log_server import BeetleHandler
    from .log_handler import _NAMED_LOGGERS

    for _ in range(10):   # up to 5 s
        await asyncio.sleep(0.5)
        try:
            handler = BeetleHandler(port=port)
            handler.setLevel(logging.DEBUG)
            for name in _NAMED_LOGGERS:
                logging.getLogger(name).addHandler(handler)
            self._beetle_handler = handler
            return
        except OSError:
            continue  # beetle not ready yet — retry
```

### Teardown

```python
# in run() finally block, alongside detach_log_handler():
if self._beetle_handler:
    for name in _NAMED_LOGGERS:
        logging.getLogger(name).removeHandler(self._beetle_handler)
    self._beetle_handler.close()
    self._beetle_handler = None
```

---

## Data flow after the change

```
Agent activity
    ↓  Python logging
TuiLogHandler.emit()          ← unchanged
    ├── state.log_lines        ← unchanged (TUI display)
    └── BeetleHandler.emit()   ← NEW: attached by _attach_beetle_handler
              ↓  JSON over TCP  127.0.0.1:9020
         beetle  log_server_loop          ← unchanged
              ↓
         BeetleSession.append_line()      ← unchanged
              ↓
         _on_log_line() → debounce → auto-analysis   ← unchanged
```

History comes from `--logs <tmpfile>`. Live updates come from `BeetleHandler`. Both paths already exist — `/interpret` just needs to use both at the same time.

---

## File summary

| File | Change |
|------|--------|
| `packages/lab_mouse/src/lab_mouse/tui/app.py` | Rewrite `_launch_beetle()`: add `--port`, add `_attach_beetle_handler()` coroutine, teardown |
| Everything else | **No changes** |

---

## Why no changes to `equator` or `beetle`

- `beetle/__main__.py` already handles `--logs + --port` together
- `BeetleHandler` already forwards live records correctly
- `log_server_loop` already receives them
- `lab_mouse/log_handler.py` already knows about `BeetleHandler` and `_NAMED_LOGGERS`

The only missing piece is `/interpret` wiring these two things together.
