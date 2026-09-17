# py2048

A 2048 implementation in Python. The engine originated as teaching code from Phil
Rodgers (University of Strathclyde) and was extended for Monte Carlo Tree Search work.
The long-term goal is an engine fast enough to sit under an AI search (A*, BFS, MCTS).

## Commands

Never activate the virtualenv; always prefix with `uv run`, which verifies the lock and
syncs first.

```bash
uv sync                             # after pulling a changed pyproject.toml or uv.lock
uv run python py2048_game.py        # console UI
uv run python py2048_pygame.py      # pygame UI
uv run behave                       # executable specs (once issue 04 lands)
pwsh .devcontainer/smoke-test.ps1   # verify the container build
```

Headless pygame (for tests and CI): `SDL_VIDEODRIVER=dummy`.

## Rules

- **Dependencies are declared with `uv add`**, never `pip install` and never by
  hand-editing `pyproject.toml` without `uv lock`. Both leave the lockfile stale.
- **`uv.lock` is committed** and there is exactly one lockfile.
- **`sys.path` manipulation is always a bug.** If an import fails, the package is not
  registered — fix that instead. See `docs/issues/11-src-layout.md`.
- **uv owns Python.** Do not add a python devcontainer feature; a second interpreter on
  PATH shadows uv's silently.

## Architecture

```
py2048_classes.py   Board + Tile. The engine. All game logic.
py2048_game.py      Console UI.
py2048_pygame.py    Pygame UI.
```

The engine/UI split is clean and worth preserving: both front-ends are independent
consumers of one `Board`, and neither reaches into the other. A third (browser) UI is
planned on the same basis — see `docs/issues/09-browser-ux.md`.

Board state is `grid[y][x]`, indexed row-then-column, with `None` for an empty cell.
Tiles store the *exponent* (`Tile(1)` renders as 2, `Tile(3)` as 8), so `get_value()`
returns the exponent and `get_tile_value()` returns `2 ** exponent`.

## Known traps

- **`Board.add_random_tiles(n)` hangs** when fewer than `n` cells are free. Confirmed,
  not theoretical. Issue 02.
- **The pygame UI is double-transposed** — `Tile.__init__` derives screen *x* from
  `row`, and `convert_grid` reads `grid[column][row]`. The two cancel and the render is
  genuinely correct, but it reads as a bug. Do not "fix" one half. Issue 07.
- **No game-over detection exists.** A dead board silently accepts input. Issue 03.
- **4-tile spawn is 20%**, not the standard 10%. Possibly deliberate; matters for
  benchmarking. Issue 08.

## Workflow

Work is issue-driven and incremental. The backlog lives in `docs/issues/`, with
sequencing and dependencies in `docs/issues/README.md`. One issue per branch, one PR
per issue.

Two ordering constraints are deliberate and should not be shortcut:

1. **The dev container comes first** — nothing is reliably runnable without it.
2. **Performance work comes strictly after the behave suite** (issue 10 after issue 04).
   The point of the optimisation is to change the board representation without changing
   behaviour, which is only safe with the specs in place.

Issue 09 (browser UX) starts with a planning session to settle architecture before any
code is written.
