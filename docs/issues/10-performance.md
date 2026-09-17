TITLE: Optimise the engine for AI search throughput
LABELS: performance
---
If the engine is to be driven by a search algorithm (A*, BFS, MCTS), move evaluation
throughput is the binding constraint. The current implementation is written for clarity,
not speed.

### Known costs
- Every tile is a `Tile` object; a board is 16 heap allocations plus a nested list.
- Moves mutate in place, so search has to deep-copy boards to explore alternatives —
  `export_state()` / re-`Board()` round-trips on every node.
- Each move runs two passes (`__scooch_*` then `__go_*_1`) over the grid.
- `add_random_tiles` probes random coordinates rather than sampling free cells
  (see #2).

### Directions worth evaluating
- Represent the board as a flat tuple of ints, or a 64-bit bitboard (4 bits per cell) —
  the standard approach for fast 2048 engines, and it makes states hashable for
  transposition tables.
- Precomputed row-move lookup tables: 65,536 entries covering every possible row, making
  a move four table lookups.
- Immutable moves returning a new board, removing copy overhead from search.

### Process
**Do not start until #4 is merged.** The test suite is what makes this safe — the whole
point is to change the representation without changing behaviour.

Establish a benchmark (moves/second) before optimising, and report before/after.

Depends on: #4.
