TITLE: Executable specifications with behave and table-driven board states
LABELS: testing
---
There are no tests. For an engine whose value is correctness under AI rollout, that is
the biggest gap in the project.

Build a Gherkin/behave suite where board state and expected result are both expressed as
readable tables, so a scenario shows the before/after grid at a glance.

Target shape:

```gherkin
Scenario: Two equal tiles merge when moved left
  Given a board
    |   |   |   |   |
    |   |   |   |   |
    |   |   |   |   |
    | 2 | 2 |   |   |
  When the player moves LEFT
  Then the board is
    |   |   |   |   |
    |   |   |   |   |
    |   |   |   |   |
    | 4 |   |   |   |
  And the score is 4
```

### Scope
- `features/` with step definitions in `features/steps/` and `environment.py`.
- A table-to-`Board` wrapper and a board-comparison helper with a readable diff on
  failure. Evaluate Polars for the grid comparison — it gives a clean tabular diff, but
  confirm it earns the dependency against a plain nested-list compare.
- Scenario Outlines for the directional symmetry cases (the same merge rule in all four
  directions).
- Seed control for `add_random_tiles` so scenarios are deterministic.

### Baseline cases (all currently pass — lock them in)
- `[2,2,2,2]` left → `[4,4,_,_]`, not `[8,_,_,_]`
- `[2,4,4,2]` left → `[2,8,2,_]`
- `[2,_,_,2]` left → `[4,_,_,_]`
- No-op moves report `False`
- Score increments by the merged tile's value
- Vertical equivalents of each

### Acceptance criteria
- `uv run behave` passes in the dev container.
- Coverage of all four directions, merge ordering, no-op detection, and scoring.

Depends on: #1. Blocks: performance work.
