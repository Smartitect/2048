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

**[docs/architecture.md](docs/architecture.md) is the full picture** — the diagrams, the
browser round trip, the JSON the AI player is sent, and where each is pinned down. Keep it
current when you change any of them; do not restate it here or in the README.

```
src/py2048/engine.py      Board + Tile. The engine. All game logic.
src/py2048/console.py     Console UI.     Entry point: py2048
src/py2048/pygame_ui.py   Pygame UI.      Entry point: py2048-pygame
src/py2048/web/           Browser UI.     Entry point: py2048-web
src/py2048/agent/         AI players. state.py builds the JSON, jev.py asks the model.
```

The invariants, which are what a change is most likely to break:

- The engine/UI split is clean: all four front-ends are independent consumers of one
  `Board`, and none reaches into another.
- Board state is `grid[y][x]`, row-then-column, `None` for empty. Tiles store the
  *exponent* (`Tile(1)` renders as 2), so `get_value()` returns the exponent and
  `get_tile_value()` returns `2 ** exponent`.
- State crosses the wire — to the browser and to the model — as tile **values**, never
  exponents.
- **No game logic in JavaScript** (#15). The page posts moves and renders what comes back.
- An AI player (#31, #33, #37, #39) only ever *chooses*; the engine decides what that does.
  Only legal moves are offered, and a fallback is never silent. Every player answers
  `choose(board, moves_played, recent_moves)` with a direction and a `decision()`, and has
  a `close()`. **Adding a player is a module in `agent/` and one line in
  `default_players()`** — never a special case in the runner, the API or the page, all of
  which read the register. `features/players.feature` runs the contract against every
  registered player; a new one has to pass it.
- The players are deliberately separate: they share `agent/player.py` (the contract) and
  `agent/board.py` (legal moves, copies) and nothing else. Judging a position belongs to
  the agent that judges it — `jev/state.py` is Jev's payload, not a shared library.
- Facts sent to the model are derived by playing the move on a copy. The random spawn is
  never stated as a consequence of a move — `could_end_the_game` is risk, not prediction.
- `agent/mcts/search.py` is a port of the MSc assignment at `Smartitect/Applying-MCTS-To-2048`,
  and its parameters are that report's measurements. Retuning them is a separate exercise
  from tidying the code, and should come with numbers. Nothing in it is async or does I/O,
  which is what lets `MctsPlayer` run it in a thread; keep it that way or it will stall the
  event stream.

## Documentation

- `README.md` is the front door: what it is, how to run it, the controls, and links onward.
- `docs/architecture.md` is the design. One place, not three.
- `docs/diagrams/*.html` are the diagram **sources**, generated with the Diagram Design
  skill; the `.png` beside each is the export used in the docs. Edit the HTML and
  re-export; do not hand-edit a PNG.
- The palette is endjin's, saved as the `endjin` Diagram Design profile and bound by the
  `.diagram-design` marker at the repository root. The browser and pygame UIs use the same
  palette, so screenshots and diagrams agree.

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
