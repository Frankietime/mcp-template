# Workspaces

<!-- last-updated: 2026-03-19 -->

> Understanding how UV manages this monorepo and routes commands to packages.

---

## How UV Workspaces Work

UV workspaces allow multiple Python packages to coexist in a single repository, sharing a **single lock file** and **virtual environment** while maintaining independent `pyproject.toml` files.

---

## 1. The Workspace Configuration

### Root pyproject.toml

The magic starts in the root `pyproject.toml`:

```toml
[project]
name = "mcp-template-workspace"       # Workspace name (not a real package)
version = "0.1.0"
requires-python = ">=3.13"

[dependency-groups]
dev = [                               # Dev tools available to ALL packages
    "pytest>=8.4.2",
    "ruff>=0.14.2",
    "ty>=0.0.12",
    # ...
]

[tool.uv.workspace]
members = ["packages/*", "mcp_server"]   # ← THIS IS THE KEY LINE
```

The `[tool.uv.workspace]` section tells UV:
- **Scan `packages/*`** → Find `mcp_shared`
- **Include `mcp_server`** → The MCP server package
- **Treat each as a member package** with its own `pyproject.toml`

---

## 2. Package Discovery Flow

When you run `uv sync --all-packages`, UV does:

```
1. Read root pyproject.toml
         │
         ▼
2. Find workspace members via glob patterns:
   • packages/* → 1 package found (mcp_shared)
   • mcp_server → 1 package found (MCP server)
         │
         ▼
3. Read each member's pyproject.toml
         │
         ▼
4. Resolve all dependencies together
         │
         ▼
5. Create single uv.lock with ALL versions
         │
         ▼
6. Install ALL packages as editable in .venv
```

### What Gets Installed

```
.venv/
├── Lib/site-packages/
│   ├── mcp_shared/             → symlink to packages/mcp_shared/src/
│   ├── mcp_server/             → symlink to mcp_server/src/
│   ├── google_adk/             → regular install
│   ├── fastmcp/                → regular install
│   ├── pydantic/               → regular install
│   └── ...
```

Verify with:
```powershell
uv pip list | Select-String "mcp"
```

Output:
```
mcp-shared           0.1.0  → C:\...\packages\mcp_shared
mcp-template-server  0.1.0  → C:\...\mcp_server
```

**Key insight**: All workspace packages are **editable installs**. Edit code → changes take effect immediately.

---

## 3. How Package Scripts Are Routed

### Defining a Script

In `mcp_server/pyproject.toml`:

```toml
[project.scripts]
mcp_server = "mcp_server.__main__:main"
#   │                │             │
#   │                │             └── Function to call
#   │                └── Module path
#   └── Command name
```

This creates an executable in `.venv/Scripts/mcp_server.exe` (Windows) or `.venv/bin/mcp_server` (Unix).

### Running the Script

```powershell
uv run mcp_server
```

---

## 4. Inter-Package Dependencies

### How Packages Reference Each Other

In `mcp_server/pyproject.toml`:

```toml
[project]
dependencies = [
    "mcp-shared",
    "fastmcp<3.0.0",
]

[tool.uv.sources]
mcp-shared = { workspace = true }
```

**Key points:**

1. **`dependencies`**: Packages from PyPI or workspace
2. **`[tool.uv.sources]`**: Routes workspace packages locally

---

## 5. The Lock File

The root `uv.lock` contains a single, unified lockfile for all workspace members.

### Benefits

- **Single source of truth** for all versions
- **Reproducible builds** across machines
- **No version conflicts** between packages

---

## 6. Quick Reference

| What You Want | Command |
|---------------|---------|
| Install everything | `uv sync --all-packages` |
| Run MCP server | `uv run mcp_server` |
| Run pytest | `uv run pytest` |
| Run any command in venv | `uv run <command>` |
| Add dependency to package | `uv add --package mcp-template-server <dep>` |
| Add dev dependency | `uv add --dev <dep>` |
| Build package wheel | `uv build --package mcp-template-server` |
| List installed packages | `uv pip list` |
| Show workspace tree | `uv tree` |

---

## Key Takeaways

1. **`[tool.uv.workspace].members`** defines which folders are packages
2. **`[tool.uv.sources]`** routes dependencies to workspace packages
3. **`[project.scripts]`** creates runnable commands
4. **All packages share one `uv.lock`** for reproducibility
5. **All packages are editable installs** - edit code, changes apply immediately
6. **Always use `uv sync --all-packages`** for this monorepo
