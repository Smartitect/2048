TITLE: Pygame coordinate handling is double-transposed
LABELS: chore
---
`Tile.__init__(row, column)` derives screen *x* from `row` (py2048_pygame.py:60-61),
while `Game.convert_grid` reads `grid[column][row]` (py2048_pygame.py:132).

The two transpositions cancel, so the rendered board is genuinely correct — verified by
asserting every cell against the board state. But the code reads as though it has a bug,
and it is a trap for the next change to the rendering path.

### Scope
Settle on one convention (board is `grid[y][x]`), make the pygame side follow it
directly, and delete the compensating transposition. Requires the test suite (#4) or an
orientation assertion to confirm the render is unchanged.
