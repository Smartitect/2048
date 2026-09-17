# py2048

A 2048 implementation in Python. The engine originated as teaching code from Phil
Rodgers (University of Strathclyde) and was extended for Monte Carlo Tree Search work.
The long-term goal is an engine fast enough to sit under an AI search (A*, BFS, MCTS).

## Commands

Never activate the virtualenv; always prefix with `uv run`, which verifies the lock and
syncs first.

```bash
uv sync                             # after pulling a changed pyproject.toml or uv.lock
uv run py2048                       # console UI
uv run py2048-pygame                # pygame UI
uv run behave                       # executable specs
uv run behave features/movement.feature  # one feature
pwsh .devcontainer/smoke-test.ps1   # verify the container build
```

Headless pygame (for tests and CI): `SDL_VIDEODRIVER=dummy`.

## Specifications

`features/` is the safety net for everything that changes the engine, and the
reason #6 can change the board representation without changing behaviour.

- Feature files speak in **tile values** (2, 4, 8); the exponent conversion lives in
  the step definitions, so a scenario reads like the screen.
- A board table is four rows with **no header**. behave reads the first row as the
  headings, and `grid_from_table` puts it back — do not add a header row to make it
  look conventional, the grid is the point.
- Rules that hold in all four directions are written once with the *line notation*:
  `the line facing <direction> is "2 2 2 ."`, where index 0 is the edge the move
  pushes toward and `.` is an empty cell. One scenario, four directions.
- `rendering.feature` drives the real pygame UI on SDL's dummy driver and asserts
  where each value lands on screen. A transposed render still looks like a plausible
  board, so orientation is the one thing worth pinning down.
- Randomness is seeded per scenario in `features/environment.py`. Assert a replay
  with the same seed rather than hard-coding spawn coordinates, which would pin the
  specs to the internals of `random.sample`.

## Rules

- **Dependencies are declared with `uv add`**, never `pip install` and never by
  hand-editing `pyproject.toml` without `uv lock`. Both leave the lockfile stale.
- **`uv.lock` is committed** and there is exactly one lockfile.
- **`sys.path` manipulation is always a bug.** If an import fails, the package is not
  registered — fix that instead. `src/py2048/` is installed by `uv sync`, so
  `from py2048 import Board` works from any directory; nothing needs a path shim.
- **uv owns Python.** Do not add a python devcontainer feature; a second interpreter on
  PATH shadows uv's silently.

## Architecture

```
src/py2048/engine.py      Board + Tile. The engine. All game logic.
src/py2048/console.py     Console UI.     Entry point: py2048
src/py2048/pygame_ui.py   Pygame UI.      Entry point: py2048-pygame
```

The engine/UI split is clean and worth preserving: both front-ends are independent
consumers of one `Board`, and neither reaches into the other. A third (browser) UI is
planned on the same basis — see #15.

Board state is `grid[y][x]`, indexed row-then-column, with `None` for an empty cell.
Tiles store the *exponent* (`Tile(1)` renders as 2, `Tile(3)` as 8), so `get_value()`
returns the exponent and `get_tile_value()` returns `2 ** exponent`.

## Known traps

- **4-tile spawn is 20%**, not the standard 10%. Possibly deliberate; matters for
  benchmarking. #14.
- **`Tile._has_merged` never changes an outcome.** The merge-once rule is already
  enforced by the move loop, so the guard and the `reset_tile_merges()` walk before
  every move are dead weight in the hot path. #20.

Fixed, and no longer traps: the `add_random_tiles` hang (#8), the pygame double
transposition (#13, now plain `grid[y][x]` on both sides), and the missing game-over
detection (#9, #23 — both UIs end the game now; pygame offers R to restart).

## Workflow

Work is issue-driven and incremental. The backlog lives in GitHub issues
(`gh issue list`). One issue per branch, one PR per issue; the PR closes the issue.

| Phase | Issues | Depends on |
|---|---|---|
| 1 — foundation | #7 dev container | — |
| 2 — correctness | #8 `add_random_tiles` hang, #9 game-over detection | #7 |
| 4 — tidy | #11 README, #12 debug leftovers, #13 pygame coordinates, #14 spawn probability | #13 needs #10 |
| 5 — features | #15 browser UX, #6 engine performance | #6 needs **#10** |

Two ordering constraints are deliberate and should not be shortcut:

1. **The dev container comes first** — nothing is reliably runnable without it.
2. **Performance work comes strictly after the behave suite** (#6 after #10).
   The point of the optimisation is to change the board representation without changing
   behaviour, which is only safe with the specs in place.

#15 (browser UX) starts with a planning session to settle architecture before any
code is written.
