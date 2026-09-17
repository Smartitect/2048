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
uv run py2048-web                   # browser UI on http://127.0.0.1:8000
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
- `web_api.feature` drives the browser API through FastAPI's `TestClient`, except for
  the event stream, which runs against a real uvicorn server on a free port — an
  in-process client cannot tear down an endless stream. `after_scenario` stops it.
- `ai_player.feature` stubs the model. What is worth pinning down is the state we send,
  that only legal moves are offered and that fallbacks say why; whether Jev plays 2048
  well is not something a specification can assert. **No spec calls the live API.**
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
src/py2048/web/           Browser UI.     Entry point: py2048-web
src/py2048/agent/         AI players. state.py builds the JSON, jev.py asks the model.
```

The engine/UI split is clean and worth preserving: all three front-ends are independent
consumers of one `Board`, and none reaches into another.

The browser UI (#15) keeps the engine authoritative: no game logic in JavaScript. The
page posts moves and renders what comes back, with state pushed over server-sent events
at `/api/events`. State crosses the wire as tile **values**, never exponents.

The AI player (#31) is a fourth consumer of the same `Board`. `agent/state.py` builds the
JSON state — including what each move *would* do, played out on a copy — and
`agent/jev.py` asks TypeSafe AI's Jev for a `Choice` between the legal directions. Two
rules hold: only legal moves are offered, so an illegal answer is unrepresentable; and a
fallback is never silent — no key, an API error or low confidence falls back to a local
policy and says so in the UI.

Board state is `grid[y][x]`, indexed row-then-column, with `None` for an empty cell.
Tiles store the *exponent* (`Tile(1)` renders as 2, `Tile(3)` as 8), so `get_value()`
returns the exponent and `get_tile_value()` returns `2 ** exponent`.

## Secrets

`TYPESAFE_API_KEY` lives in `.env` at the repository root, which is gitignored; `.env.example`
is committed. It is read server-side in `web/app.py` and never reaches the browser. With no
key set everything still runs — the AI player falls back to a local policy, marked as such.

## Known traps

Fixed, and no longer traps: the `add_random_tiles` hang (#8); the pygame double
transposition (#13, now plain `grid[y][x]` on both sides); the missing game-over
detection (#9, #23 — both UIs end the game, and pygame offers R to restart); and the
`has_merged` guard (#20 — the merge-once rule is enforced by the move loop and pinned
by `features/symmetry.feature`, so do not re-add the flag without a failing case); and
the non-standard spawn rate (#14 — now `FOUR_SPAWN_PROBABILITY = 0.1`, so scores are
comparable with published 2048 benchmarks, and scores recorded before it are not).

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
