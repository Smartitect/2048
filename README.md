# 2048

Implementation of the popular 2048 game in Python, with an engine built to sit under an
AI search such as Monte Carlo Tree Search.

![The pygame user interface](images/pygame-ui.png)

## Running the game

The project is developed in a dev container, which brings its own Python, [uv], PowerShell
and the GitHub CLI. Open the repository in VS Code and choose **Reopen in Container**;
everything below then works with no further setup.

```bash
uv run py2048           # console user interface
uv run py2048-pygame    # pygame user interface
```

Outside the dev container you need [uv] and Python 3.12. `uv run` syncs the environment
from `uv.lock` before it runs anything, so there is no separate install step and no
virtualenv to activate.

### Controls

The pygame UI uses the arrow keys. **R** starts a new game and **Esc** quits. When no
move is left, the board dims and reports the final score.

The console UI is keyboard driven too, and prints the board as text:

| Key | Action |
|---|---|
| `w` | move UP |
| `s` | move DOWN |
| `a` | move LEFT |
| `d` | move RIGHT |
| `q` | quit |

```
Number of successful moves:58, Last move attempted:UP:, Move status:True
Score:372, Merge count:46, Max tile:32, Max tile coords:(2,1)
-------------------------------------
|   4    |   8    |   4    |   2    |
-------------------------------------
|   32   |   16   |   8    |   4    |
-------------------------------------
|   8    |   2    |   32   |        |
-------------------------------------
|   4    |   16   |        |   2    |
-------------------------------------
```

## Architecture

![Architecture overview](images/Core%20Game%20Architecture.png)

```
src/py2048/engine.py      Board + Tile. The engine: all game logic.
src/py2048/console.py     Console UI.    Entry point: py2048
src/py2048/pygame_ui.py   Pygame UI.     Entry point: py2048-pygame
```

Both front-ends are independent consumers of one `Board`, and neither reaches into the
other. That split is what lets the engine be driven by a search algorithm instead of a
keyboard, and it is worth preserving.

Two conventions are worth knowing before reading the code:

- Board state is `grid[y][x]` — row first, then column — with `None` for an empty cell.
- Tiles store the **exponent**, so `Tile(1)` renders as 2 and `Tile(3)` as 8.
  `get_value()` returns the exponent, `get_tile_value()` returns `2 ** exponent`.

The engine's public surface is the package itself:

```python
from py2048 import Board

board = Board()
board.add_random_tiles(2)
board.make_move("LEFT")     # True if the board changed
board.can_move()            # False once the game is over
board.export_state()        # the grid as a list of lists, for rollouts
```

## Specifications

Behaviour is pinned down by an executable specification suite, written in Gherkin and run
with [behave]:

```bash
uv run behave                            # the whole suite
uv run behave features/movement.feature  # one feature
```

Scenarios show the board before and after a move as a table, so a rule reads the way the
game looks:

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

The suite covers merge rules in all four directions, no-op detection, scoring, tile
spawning and game over, and it renders the pygame UI headlessly to check that the board is
drawn the right way round.

## Background

The bulk of this code was provided by Phil Rodgers at the University of Strathclyde. It
was subsequently extended during an assignment applying Monte Carlo Tree Search to the
game:

- Ability to initialise the `Board` class with a given state — useful for rolling the
  board out from a given position.
- A more friendly print-out of the game state.
- Score-updating methods also track a **merge count**: the total number of times two tiles
  have been combined during a game. It was explored as an alternative performance measure
  to the score, on the theory that the score may make an algorithm too greedy.
- A method returning the **max tile** and its position on the grid.
- A method to export the board state as a simple list of lists.

## Contributing

Work is issue driven: the backlog lives in [GitHub issues], one issue per branch and one
pull request per issue. `CLAUDE.md` records the conventions, the commands and the traps
worth knowing before changing anything.

[uv]: https://docs.astral.sh/uv/
[behave]: https://behave.readthedocs.io/
[GitHub issues]: https://github.com/Smartitect/2048/issues
