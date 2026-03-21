# Creating Workspace Packages

<!-- last-updated: 2026-03-19 -->

> Guide for adding new shared packages to this UV workspace.

---

## Directory Structure

Create the following structure under `packages/`:

```
packages/<package_name>/
├── pyproject.toml
└── src/
    └── <package_name>/
        ├── __init__.py
        └── py.typed        # For type hints
```

---

## Package Configuration

Create `packages/<package_name>/pyproject.toml`:

```toml
[project]
name = "<package-name>"      # Use hyphens (e.g., "mcp-shared")
version = "0.1.0"
description = "..."
requires-python = ">=3.13"
dependencies = [...]

[tool.uv]
package = true

[build-system]
requires = ["uv_build>=0.9.26,<0.10.0"]
build-backend = "uv_build"
```

---

## Consuming the Package

Add as a workspace dependency in the consumer's `pyproject.toml`:

```toml
dependencies = [..., "<package-name>"]

[tool.uv.sources]
<package-name> = { workspace = true }
```

---

## Install

```powershell
uv sync --all-packages
```

---

## Key Points

| Aspect | Convention |
|--------|------------|
| Package name | Use **hyphens** (`mcp-shared`) |
| Folder/import name | Use **underscores** (`mcp_shared`) |
| Root config | No changes needed - `packages/*` glob auto-discovers |
| Workspace source | Links packages without version pinning |
| Shared deps | Move to shared package to avoid duplication |

---

## Current Workspace Packages

| Package | Location | Description |
|---------|----------|-------------|
| `mcp-shared` | `packages/mcp_shared/` | Shared utilities — response builders, schemas, logging |
| `mcp-template-server` | `mcp_server/` | MCP Template Server |
