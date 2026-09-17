TITLE: Remove debug leftovers
LABELS: chore
---
Small cleanups found during review:

- `print("main code")` — leftover debug output (py2048_game.py:35).
- `add_tile_result` assigned and never read, in both UIs
  (py2048_game.py:63, py2048_pygame.py:182).

Low priority, but trivial to clear.
