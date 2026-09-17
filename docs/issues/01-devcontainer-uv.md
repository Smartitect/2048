TITLE: Dev container with uv, PowerShell and GitHub CLI
LABELS: infrastructure
---
The original environment is unrecoverable: `Pipfile` pins Python 3.8, no virtualenv
survives on this machine, and `pipenv` is not installed. The code itself runs fine on
Python 3.12 with pygame 2.6.1 (verified), so the tooling is the only thing that is stale.

Replace it with a reproducible dev container.

### Scope
- `.devcontainer/devcontainer.json` on a public base image plus features.
- **PowerShell** feature, used for the post-create script.
- **GitHub CLI** feature, so `gh auth login` works inside the container and issues/PRs
  can be managed from the dev environment.
- **uv owns Python** — no python devcontainer feature (a second interpreter on PATH
  shadows uv's silently).
- Migrate `Pipfile` / `Pipfile.lock` to `pyproject.toml` + `uv.lock`; delete both.
- Pin the interpreter in `.python-version`.
- `postCreateCommand` runs `.devcontainer/postCreateCommand.ps1`, ending in `uv sync`.
- `UV_CACHE_DIR` inside the workspace so rebuilds do not re-download; `.uv-cache/`
  added to `.gitignore` and hidden from the editor tree.
- Generate a PowerShell profile that auto-activates `.venv`, so no one has to remember.

### Acceptance criteria
- Container builds from a clean clone with no manual steps.
- `python --version` reports the pinned version **from `.venv`**, not a system Python.
- `pwsh`, `gh` and `uv` are all on PATH.
- `uv run python py2048_game.py` starts the console game.
- `Pipfile` and `Pipfile.lock` are gone.

Blocks: every other issue.
