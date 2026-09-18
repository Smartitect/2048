# Architecture

py2048 is a 2048 engine with three user interfaces and an AI player, built so the engine
can eventually sit under a search algorithm — A\*, BFS, Monte Carlo Tree Search — instead
of a keyboard.

This document is the one place the design is written down. The README says how to run it;
`CLAUDE.md` records the working rules for changing it.

---

## One engine, four consumers

![The engine and its four consumers](diagrams/architecture-overview.png)

```
src/py2048/engine.py      Board + Tile. The engine: all game logic.
src/py2048/console.py     Console UI.    Entry point: py2048
src/py2048/pygame_ui.py   Pygame UI.     Entry point: py2048-pygame
src/py2048/web/           Browser UI.    Entry point: py2048-web
src/py2048/agent/         AI players.    Board state in, one direction out
```

Every front-end is an independent consumer of one `Board`, and none reaches into another.
That split is the load-bearing decision in the repository: it is what lets the engine be
driven by a search algorithm rather than a person, and it is why the browser UI can hold
no game logic at all.

The engine's public surface is the package itself:

```python
from py2048 import Board

board = Board()
board.add_random_tiles(2)
board.make_move("LEFT")     # True if the board changed
board.can_move()            # False once the game is over
board.export_state()        # the grid as a list of lists, for rollouts
```

`export_state` and the `initial_state` constructor argument are the rollout pair: they let
any consumer copy a position, play it out, and throw the copy away. The AI player is built
entirely on them.

### Two conventions worth knowing before reading the code

- **Board state is `grid[y][x]`** — row first, then column — with `None` for an empty cell.
  Both the pygame UI and the browser UI index it the same way round; there is no transpose
  anywhere, and `features/rendering.feature` exists to keep it that way.
- **Tiles store the exponent.** `Tile(1)` renders as 2 and `Tile(3)` as 8. `get_value()`
  returns the exponent, `get_tile_value()` returns `2 ** exponent`. State crosses the wire
  to the browser and to the model as tile **values**, never exponents.

---

## The browser round trip

The browser UI keeps the engine authoritative. The page captures a key, posts it, and
renders whatever comes back; no rule is implemented twice.

State reaches the browser two ways: a snapshot at `GET /api/state`, and a push over
server-sent events at `GET /api/events`. The board only changes when the engine says so,
which is the shape SSE fits — and because every change broadcasts to all subscribers, two
open tabs stay in step and a search driving the same session needs no extra machinery.

| Endpoint | Does |
|---|---|
| `GET /api/state` | The current state, as tile values |
| `POST /api/move` | Play one direction; returns whether the board changed |
| `POST /api/new` | Start again. An AI player already playing keeps going |
| `POST /api/agent/start` · `/stop` | Hand the game to the AI player, or take it back |
| `GET /api/events` | The state stream, with a heartbeat every 15s |

When the AI player is driving, one move looks like this:

![One move, chosen by Jev](diagrams/ai-move-sequence.png)

`AgentRunner` holds the loop and knows nothing about HTTP: it asks a player for a move,
applies it through the session, and waits. Because every move goes through the session,
the browser sees the AI's moves over the stream it is already listening to.

---

## What the AI player is told

`agent/state.py` builds the JSON state; `agent/jev.py` asks [TypeSafe AI's Jev][jev] for a
`Choice` between the legal directions. Two rules hold: **only legal moves are offered**, so
an illegal answer is unrepresentable; and **a fallback is never silent** — no key, an API
error, or a confidence below the threshold falls back to a local policy and says so on
screen.

The design principle is that the engine does the arithmetic and the model does the judging.
Every figure below is measured by copying the board and playing the move on the copy, so
the facts cannot drift from the rules:

![Where the facts come from](diagrams/state-provenance.png)

### `board` — what is true right now

| Field | Says |
|---|---|
| `grid` | The board as tile values, `grid[row][column]`, `null` for empty |
| `score` | The running score |
| `empty_cells` | How much room is left |
| `largest_tile`, `largest_tile_cell` | The biggest tile and where it sits |
| `largest_tile_in_corner` | Whether it is anchored |
| `merges_available` | Adjacent equal pairs on the board now |
| `monotonicity` | 0–1: how well the tiles step down from the corner nearest the largest tile |

`monotonicity` is the heuristic every strong 2048 player uses, stated as a number. 1.0 is a
clean staircase, which is what keeps merges lining up. It is measured from whichever corner
the game is already built into, because which corner that is is the game's own business.

### `history` — what has been happening

| Field | Says |
|---|---|
| `moves_played` | How long this game has run |
| `recent_moves` | The last six directions played, oldest first |

Each call is otherwise stateless. Without `recent_moves`, a game ping-ponging LEFT and
RIGHT looks exactly like any other position.

### `available_moves[direction]` — what each move would do

Only directions the engine would accept appear here. Everything is the position the move
produces, *before* the random tile that spawns after it.

| Field | Says |
|---|---|
| `points_gained`, `tiles_merged` | What the move scores |
| `empty_cells_after`, `empty_cells_gained` | The room it leaves, and the change |
| `largest_tile_stays_in_corner` | Whether it keeps the big tile anchored |
| `moves_available_after` | The directions still legal afterwards |
| `merges_available_after` | The merges it sets up for the turn after |
| `monotonicity_after`, `monotonicity_change` | What it does to the ordering |
| `could_end_the_game` | Whether a spawn on the resulting board could leave no move |
| `board_after` | The resulting grid, as tile values |

`moves_available_after` and `could_end_the_game` are the two that carry danger. Without
them, a move that leaves one legal direction is indistinguishable from one that leaves
three.

### Certainty and risk are kept apart

Everything above but `could_end_the_game` is certain — it is the position the engine would
produce. The spawn is random, so it is never stated as a consequence of choosing a
direction.

`could_end_the_game` is the one exception, and it is deliberately framed as risk rather
than prediction: it says the position after this move *has* a spawn that leaves no legal
move, not that the spawn will happen. It is cheap to answer, because a spawn fills one cell
and a board with a free cell always has a move — so only a board with exactly one free cell
can be dead after a spawn, which takes two probes to check.

### The criteria carry the same facts

The `Choice` criterion is the text the decision is actually made against, so it restates
the JSON rather than summarising it:

```
Move DOWN:  merges nothing, leaves 4 empty cells, keeps the largest tile in a corner,
            leaves 3 legal direction(s), sets up 1 mergeable pair(s),
            tile ordering 0.75 (-0.21).
Move RIGHT: merges nothing, leaves 4 empty cells, keeps the largest tile in a corner,
            leaves 3 legal direction(s), sets up 3 mergeable pair(s),
            tile ordering 0.88 (-0.08).
```

Both leave the same room and both keep the big tile anchored. Only the last two clauses
separate them.

### What is deliberately left out

- **The spawn itself.** Naming a cell the tile "will" appear in would be a guess presented
  as a fact.
- **The whole move transcript.** Six moves is enough to show a game going in circles; more
  is a transcript to read rather than a position to judge.
- **A recommendation.** Which move is best is the question being asked, not part of the
  state.
- **Deeper rollouts.** One ply is measured. Two would multiply the payload and start
  guessing at spawns, which is search — and search belongs in the engine (issue #6), not in
  the prompt.

---

## Where this is pinned down

`features/` is the safety net for everything that changes the engine, and the reason the
board representation can be optimised without changing behaviour.

| Feature file | Pins down |
|---|---|
| `movement.feature`, `symmetry.feature` | Merge and slide rules, in all four directions |
| `no_op_moves.feature` | A move that changes nothing is refused |
| `spawning.feature` | Where and how often tiles appear |
| `game_over.feature` | When there is no move left |
| `rendering.feature` | That the pygame UI draws the board the right way round |
| `pygame_controls.feature` | Keys, restart, quit |
| `web_api.feature` | The endpoints and the event stream |
| `ai_player.feature` | The state we send, legal-moves-only, and visible fallbacks |

Scenarios speak in tile values, and a board is four rows with no header row — behave reads
the first row as headings and `grid_from_table` puts it back. Rules that hold in all four
directions are written once with the line notation, and randomness is seeded per scenario
so a replay can be asserted instead of a hard-coded spawn coordinate.

No specification calls the live model.

---

## The diagrams

The diagrams above are generated, not drawn. Each one is a self-contained HTML file in
[`diagrams/`](diagrams/) — that is the source — and the committed `.png` beside it is the
export used in this document.

They use endjin's web palette, stored as a Diagram Design profile. The project's
`.diagram-design` marker binds the repository to it, so a new diagram picks up the same
skin without being told:

```
~/.diagram-design/profiles/endjin.md   the profile
.diagram-design                        profile: endjin
```

The profile lives outside the repository, so a fresh machine will not have it. It was
generated by reading the custom properties out of endjin.com's stylesheet, and can be
regenerated the same way; the tokens themselves are recorded in the profile's header.

To change a diagram, edit its HTML and re-export it to PNG at 2× with a headless browser.
The browser UI and the pygame UI use the same palette, so the screenshots and the diagrams
agree.

[jev]: https://docs.typesafe.ai/introduction
