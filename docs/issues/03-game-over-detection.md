TITLE: No game-over detection
LABELS: enhancement
---
`Board` exposes `is_board_full()` but has no way to ask whether any legal move remains.
On a full interlocked board all four moves return `False` and both UIs keep accepting
keypresses that silently do nothing — the game never ends.

```python
full = [[1,2,1,2],[2,1,2,1],[1,2,1,2],[2,1,2,1]]
# every move returns False; no UI reacts
```

### Scope
- Add `Board.can_move()` (any direction produces a change) — must not mutate the board.
- Console UI: detect and report game over, then exit or offer restart.
- Pygame UI: render a game-over state.

Depends on: a decision about whether `can_move()` works on a copy or by simulation.
