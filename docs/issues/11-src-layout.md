TITLE: Restructure engine into an installable src/ package
LABELS: infrastructure
---
The engine modules sit at the repository root (`py2048_classes.py`, `py2048_game.py`,
`py2048_pygame.py`) and are imported only because the interpreter's working directory
happens to be on `sys.path`.

That holds for `python py2048_game.py`. It stops holding as soon as `tests/` needs to
import the engine, and the usual workaround — a `sys.path.insert` in `environment.py` —
is exactly the bug it looks like.

### Scope
- `src/py2048/` holding the engine (`Board`, `Tile`), re-exported from `__init__.py`.
- Front-ends move out of the import root: console and pygame UIs become entry points.
- Register the package in `[tool.hatch.build.targets.wheel] packages` and drop
  `[tool.uv] package = false`.
- `uv sync` then makes `from py2048 import Board` work from anywhere.
- Optionally expose `[project.scripts]` entry points so the games launch by name.

### Why now and not later
Doing this *before* #4 means the test suite is written against the final import shape.
Doing it after means rewriting every step definition.

Depends on: #1. Should land before: #4.
