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
uv run behave                       # executable specs (once #10 lands)
pwsh .devcontainer/smoke-test.ps1   # verify the container build
```

Headless pygame (for tests and CI): `SDL_VIDEODRIVER=dummy`.

## Rules

- **Dependencies are declared with `uv add`**, never `pip install` and never by
  hand-editing `pyproject.toml` without `uv lock`. Both leave the lockfile stale.
- **`uv.lock` is committed** and there is exactly one lockfile.
- **`sys.path` manipulation is always a bug.** If an import fails, the package is not
  registered — fix that instead. See #16.
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
planned on the same basis — see #15.

Board state is `grid[y][x]`, indexed row-then-column, with `None` for an empty cell.
Tiles store the *exponent* (`Tile(1)` renders as 2, `Tile(3)` as 8), so `get_value()`
returns the exponent and `get_tile_value()` returns `2 ** exponent`.

## Known traps

- **`Board.add_random_tiles(n)` hangs** when fewer than `n` cells are free. Confirmed,
  not theoretical. #8.
- **The pygame UI is double-transposed** — `Tile.__init__` derives screen *x* from
  `row`, and `convert_grid` reads `grid[column][row]`. The two cancel and the render is
  genuinely correct, but it reads as a bug. Do not "fix" one half. #13.
- **No game-over detection exists.** A dead board silently accepts input. #9.
- **4-tile spawn is 20%**, not the standard 10%. Possibly deliberate; matters for
  benchmarking. #14.

## Workflow

Work is issue-driven and incremental. The backlog lives in GitHub issues
(`gh issue list`). One issue per branch, one PR per issue; the PR closes the issue.

| Phase | Issues | Depends on |
|---|---|---|
| 1 — foundation | #7 dev container | — |
| 2 — correctness | #8 `add_random_tiles` hang, #9 game-over detection | #7 |
| 3 — safety net | #16 `src/` layout, then #10 behave specs | #7; #10 needs #16 |
| 4 — tidy | #11 README, #12 debug leftovers, #13 pygame coordinates, #14 spawn probability | #13 needs #10 |
| 5 — features | #15 browser UX, #6 engine performance | #6 needs **#10** |

Two ordering constraints are deliberate and should not be shortcut:

1. **The dev container comes first** — nothing is reliably runnable without it.
2. **Performance work comes strictly after the behave suite** (#6 after #10).
   The point of the optimisation is to change the board representation without changing
   behaviour, which is only safe with the specs in place.

#15 (browser UX) starts with a planning session to settle architecture before any
code is written.
