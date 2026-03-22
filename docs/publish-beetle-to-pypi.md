# Publishing beetle to PyPI

This tutorial walks through everything needed to make `beetle` publicly installable via `pip install beetle`. Because beetle depends on the `tui` workspace package, both packages must be published to PyPI.

---

## Prerequisites

- Python 3.13+
- `uv` installed (`pip install uv` or [docs](https://docs.astral.sh/uv/))
- A [PyPI account](https://pypi.org/account/register/)
- A [TestPyPI account](https://test.pypi.org/account/register/) (separate from PyPI — used for dry-runs)

---

## Step 1 — Reserve the package names on PyPI

> Do this before writing a single line of metadata. Package names on PyPI are first-come, first-served.

1. Log in to [pypi.org](https://pypi.org)
2. Search for `beetle` and `tui`

> **Warning:** `tui` is extremely generic and almost certainly taken. Check now. If it is, rename the package in `packages/tui/pyproject.toml` to something like `beetle-tui` or `beetle-core` — then update the dependency in beetle's `pyproject.toml` accordingly.

---

## Step 2 — Create API tokens

You need one token per package, or a single scoped account token.

1. Go to **PyPI → Account settings → API tokens**
2. Click **Add API token**
3. Scope: **Entire account** (for first upload — you can scope to project after the first release)
4. Copy the token. **It will not be shown again.**
5. Store it safely:

```bash
# Add to your shell profile or a .env file (never commit this)
export PYPI_TOKEN="pypi-..."
```

Repeat on **TestPyPI** for dry-run uploads.

---

## Step 3 — Enrich `packages/tui/pyproject.toml`

```toml
[project]
name = "beetle-tui"          # rename if "tui" is taken — check Step 1
version = "0.1.0"
description = "Shared prompt_toolkit TUI foundation for beetle"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.13"
authors = [{ name = "Your Name", email = "you@example.com" }]
keywords = ["tui", "terminal", "prompt-toolkit"]
classifiers = [
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.13",
]

[project.urls]
Repository = "https://github.com/your-org/mcp-template"

dependencies = [
    "prompt-toolkit>=3.0.51",
]

[tool.uv]
package = true

[build-system]
requires = ["uv_build>=0.9.26,<0.10.0"]
build-backend = "uv_build"
```

---

## Step 4 — Enrich `packages/beetle/pyproject.toml`

Two changes here: add PyPI metadata **and** replace the workspace dependency on `tui` with the published package name and version.

```toml
[project]
name = "beetle"
version = "0.1.0"
description = "Beetle (=){ — logging-first developer tool for AI projects"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.13"
authors = [{ name = "Your Name", email = "you@example.com" }]
keywords = ["logging", "tui", "llm", "debugging", "pydantic-ai", "ollama"]
classifiers = [
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Debuggers",
]

[project.urls]
Repository = "https://github.com/your-org/mcp-template"
"Bug Tracker" = "https://github.com/your-org/mcp-template/issues"

dependencies = [
    "pydantic-ai>=0.2.0",
    "prompt-toolkit>=3.0.51",
    "python-dotenv>=1.0.0",
    "beetle-tui>=0.1.0",   # <-- was: tui = { workspace = true }
]

[project.scripts]
beetle = "beetle.__main__:main"

[tool.uv]
package = true

# Keep workspace resolution working locally while the published name is beetle-tui
[tool.uv.sources]
beetle-tui = { workspace = true }

[build-system]
requires = ["uv_build>=0.9.26,<0.10.0"]
build-backend = "uv_build"
```

> The `[tool.uv.sources]` block makes `uv` resolve `beetle-tui` from the local workspace during development, while the published package references it by PyPI name. This is the uv-native way to handle monorepo + public package coexistence — no duplication, no hacks.

---

## Step 5 — Add a README to `tui`

PyPI requires a README for the long description. Add a minimal one:

```bash
echo "# beetle-tui\n\nShared prompt_toolkit TUI foundation for the beetle package." \
  > packages/tui/README.md
```

---

## Step 6 — Dry-run on TestPyPI

Always validate on TestPyPI before touching the real index.

```bash
# Build both packages from the workspace root
uv build --package beetle-tui
uv build --package beetle

# Inspect what was built
ls dist/
# beetle_tui-0.1.0-py3-none-any.whl
# beetle_tui-0.1.0.tar.gz
# beetle-0.1.0-py3-none-any.whl
# beetle-0.1.0.tar.gz

# Upload tui first (beetle depends on it)
uv publish \
  --publish-url https://test.pypi.org/legacy/ \
  --token $TEST_PYPI_TOKEN \
  dist/beetle_tui-*

# Upload beetle
uv publish \
  --publish-url https://test.pypi.org/legacy/ \
  --token $TEST_PYPI_TOKEN \
  dist/beetle-*
```

Verify the install works from TestPyPI:

```bash
pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  beetle

beetle --help
```

> `--extra-index-url pypi.org/simple/` lets pip fall back to real PyPI for `pydantic-ai` and other deps that are not on TestPyPI.

---

## Step 7 — Publish to real PyPI

```bash
# tui first
uv publish \
  --token $PYPI_TOKEN \
  dist/beetle_tui-*

# then beetle
uv publish \
  --token $PYPI_TOKEN \
  dist/beetle-*
```

Verify:

```bash
pip install beetle
beetle --help
```

---

## Step 8 — Automate releases with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - "[0-9]+.[0-9]+.[0-9]+"   # triggers on version tags like 0.2.0

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write   # required for trusted publishing (no token needed)

    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.13"

      - name: Build packages
        run: |
          uv build --package beetle-tui
          uv build --package beetle

      - name: Publish to PyPI (trusted publishing)
        run: uv publish dist/*
```

### Trusted Publishing (recommended — no API token in CI)

Trusted Publishing lets PyPI verify your identity via GitHub Actions OIDC — no stored secrets.

1. Go to **PyPI → your project → Publishing → Add a new publisher**
2. Fill in:
   - **Owner:** your GitHub org/username
   - **Repository:** `mcp-template`
   - **Workflow:** `publish.yml`
   - **Environment:** leave blank (or set a GitHub Environment)
3. Repeat for `beetle-tui`

With this in place, the workflow above publishes without `--token` — the `id-token: write` permission handles auth automatically.

---

## Step 9 — Release workflow

This repo already uses Commitizen. The release loop is:

```bash
# 1. Bump version (updates pyproject.toml files + generates CHANGELOG)
uv run cz bump

# 2. Push the tag — this triggers the publish workflow
git push && git push --tags
```

Commitizen is configured in the root `pyproject.toml` to update all `packages/*/pyproject.toml` version fields in one bump.

---

## Checklist

- [ ] `tui` package name available on PyPI (or renamed to `beetle-tui`)
- [ ] PyPI API tokens created (or Trusted Publishing configured)
- [ ] Both `pyproject.toml` files have `readme`, `license`, `authors`, `classifiers`
- [ ] `tui` dependency in beetle changed from workspace path to versioned PyPI name
- [ ] `[tool.uv.sources]` keeps local resolution working
- [ ] TestPyPI dry-run passes
- [ ] `pip install beetle && beetle --help` works clean
- [ ] GitHub Actions publish workflow in place
- [ ] Trusted Publishing configured on PyPI for both packages
