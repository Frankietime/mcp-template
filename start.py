"""Start both mcp_server and lab_mouse with a single command.

    uv run python start.py

mcp_server launches in a new terminal window, then this script waits until
the server's healthcheck responds before starting lab_mouse in the current
terminal.  When lab_mouse exits (Ctrl+X), mcp_server is terminated.
"""

from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.request

_HEALTHCHECK_URL = "http://127.0.0.1:8000/healthcheck"
_POLL_INTERVAL = 0.5
_MAX_WAIT_SECONDS = 30


def _wait_for_server() -> bool:
    """Poll the healthcheck endpoint until the server responds or timeout."""
    deadline = time.monotonic() + _MAX_WAIT_SECONDS
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(_HEALTHCHECK_URL, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(_POLL_INTERVAL)
    return False


def main() -> None:
    # ── 1. Launch mcp_server in a separate terminal window ──────────────────
    if sys.platform == "win32":
        server_proc = subprocess.Popen(
            ["uv", "run", "mcp_server"],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    else:
        server_proc = subprocess.Popen(
            ["uv", "run", "mcp_server"],
            start_new_session=True,
        )

    # ── 2. Wait for the server to be ready ──────────────────────────────────
    print("Starting mcp_server…", flush=True)
    if not _wait_for_server():
        print(
            f"ERROR: mcp_server did not become ready within {_MAX_WAIT_SECONDS}s. "
            "Check the server terminal for errors.",
            file=sys.stderr,
        )
        server_proc.terminate()
        sys.exit(1)

    print("mcp_server ready → launching lab_mouse", flush=True)

    # ── 3. Run lab_mouse in the foreground (blocks until user quits) ────────
    try:
        subprocess.run(["uv", "run", "lab_mouse"])
    finally:
        # ── 4. Tear down mcp_server when lab_mouse exits ─────────────────────
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(server_proc.pid)],
                capture_output=True,
            )
        else:
            server_proc.terminate()


if __name__ == "__main__":
    main()
