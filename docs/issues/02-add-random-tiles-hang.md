TITLE: add_random_tiles() hangs when n exceeds the number of free cells
LABELS: bug
---
`Board.add_random_tiles()` checks `is_board_full()` once on entry, then loops
`while n > 0` picking random coordinates until it has placed `n` tiles. If fewer than
`n` cells are free, it spins forever.

Reproduced — this never returns:

```python
from py2048_classes import Board
b = Board(initial_state=[[1,2,1,2],[2,1,2,1],[1,2,1,2],[2,1,2,None]])
b.add_random_tiles(2)   # one free cell, two tiles requested
```

Neither UI triggers this today (both only ever request 1 tile after a move that
guaranteed a free cell), but the stated purpose of this fork is MCTS rollouts from
arbitrary board states, which is exactly where it bites.

The random-probe approach is also needlessly slow on a nearly-full board.

### Proposed fix
Collect the empty coordinates, place `min(n, len(empties))` tiles by sampling from that
list, and return whether all `n` were placed.

Source: py2048_classes.py:80-94
