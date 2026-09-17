"""
Turning a Board into the JSON state an AI player is asked about.

The engine already knows what each move would do, so it says so rather than
leaving the model to simulate 2048 in its head: the code does the arithmetic,
the model does the judging. Everything here is derived by playing the move on a
copy, so the facts cannot drift from the rules.

Three kinds of fact cross the wire, and the distinction is worth keeping:

- What is true of the board now - its shape, its room, the merges it has.
- What a move would certainly do, played out on a copy. The spawn that follows
  a real move is left out of these: it is random, so it is not a consequence of
  choosing this direction and has no business being stated as one.
- What a move would risk. `could_end_the_game` is the one of these, and it is a
  consequence of the choice rather than a prediction of the spawn: it says the
  position after this move has a spawn that leaves no legal move, not that the
  spawn will happen.

Nothing in this module talks to a model, which is what makes it easy to check.
"""

from ..engine import Board, Tile, FOUR, TWO

DIRECTIONS = ("UP", "DOWN", "LEFT", "RIGHT")

CORNERS = ((0, 0), (3, 0), (0, 3), (3, 3))

# Enough history to show a direction being repeated with nothing to show for
# it, and short enough that the model is not reading a transcript.
RECENT_MOVES = 6

# Every pair of neighbouring cells, counted once per axis: 12 across, 12 down.
ADJACENT_PAIRS = 24


def copy_board(board):
    """A board that can be played on without disturbing the original."""
    return Board(
        initial_state=board.export_state(),
        initial_score=board.score,
        initial_merge_count=board.merge_count,
    )


def values(board):
    """The grid as tile values, the way a player sees it."""
    return [
        [None if tile is None else tile.get_tile_value() for tile in row]
        for row in board.grid
    ]


def empty_count(board):
    return len(board.get_empty_cells())


def largest_tile(board):
    return board.get_max_tile()[0]


def largest_tile_cell(board):
    """Where the largest tile sits, or None on an empty board."""
    _, row, column = board.get_max_tile()
    if row is None:
        return None
    return {"row": row, "column": column}


def max_tile_in_corner(board):
    grid = values(board)
    largest = max((cell for row in grid for cell in row if cell), default=0)
    return any(grid[y][x] == largest for x, y in CORNERS)


def merges_available(board):
    """Adjacent equal pairs: the merges this board has on offer right now.

    A line of three equal tiles counts twice, which is right - it has two
    neighbouring pairs, and either of them can be merged.
    """
    grid = board.export_state()
    pairs = 0
    for y in range(4):
        for x in range(4):
            value = grid[y][x]
            if value is None:
                continue
            if x + 1 < 4 and grid[y][x + 1] == value:
                pairs += 1
            if y + 1 < 4 and grid[y + 1][x] == value:
                pairs += 1
    return pairs


def anchor_corner(board):
    """The corner the largest tile is nearest, as (row, column).

    Which corner a board is organised around is the board's own business - a
    game built into the bottom left is no worse than one built into the top
    right - so the ordering below is measured from wherever the big tile
    already is rather than from a corner chosen in advance.
    """
    _, row, column = board.get_max_tile()
    if row is None:
        return (0, 0)
    return (0 if row <= 1 else 3, 0 if column <= 1 else 3)


def monotonicity(board):
    """How well the tiles step down from the anchor corner, from 0 to 1.

    The heuristic every strong 2048 player uses, stated as a number: 1.0 means
    no neighbouring pair grows as it moves away from the big tile, so the board
    is a clean staircase and merges keep lining up. Empty cells count as zero,
    which rewards keeping the tiles packed towards the corner rather than
    strewn about.
    """
    grid = [[0 if cell is None else cell for cell in row] for row in board.export_state()]
    anchor_row, anchor_column = anchor_corner(board)
    ordered = 0
    for y in range(4):
        for x in range(3):
            near, far = (x, x + 1) if anchor_column == 0 else (3 - x, 2 - x)
            ordered += grid[y][near] >= grid[y][far]
    for x in range(4):
        for y in range(3):
            near, far = (y, y + 1) if anchor_row == 0 else (3 - y, 2 - y)
            ordered += grid[near][x] >= grid[far][x]
    return round(ordered / ADJACENT_PAIRS, 2)


def available_directions(board):
    """Every direction that would change this board."""
    return [
        direction for direction in DIRECTIONS if copy_board(board).make_move(direction)
    ]


def could_end_the_game(board):
    """Whether a spawn on this board could leave no legal move at all.

    A spawn fills one cell, and a board with a free cell always has a move, so
    only a board with exactly one free cell can be dead after one. That makes
    this cheap to answer, and it is the one thing a model cannot work out from
    the board alone without playing 2048 in its head.
    """
    empty = board.get_empty_cells()
    if len(empty) != 1:
        return False
    (x, y), = empty
    for exponent in (TWO, FOUR):
        probe = copy_board(board)
        probe.grid[y][x] = Tile(exponent)
        if not probe.can_move():
            return True
    return False


def outcome(board, direction):
    """What this direction would do, played out on a copy.

    Everything here but `could_end_the_game` is certain: it is the position the
    engine would produce, before the random spawn that follows a real move.
    """
    after = copy_board(board)
    moved = after.make_move(direction)
    if not moved:
        return None
    before_order = monotonicity(board)
    after_order = monotonicity(after)
    return {
        "legal": True,
        "points_gained": after.score - board.score,
        "tiles_merged": after.merge_count - board.merge_count,
        "empty_cells_after": empty_count(after),
        "empty_cells_gained": empty_count(after) - empty_count(board),
        "largest_tile_stays_in_corner": max_tile_in_corner(after),
        "moves_available_after": available_directions(after),
        "merges_available_after": merges_available(after),
        "monotonicity_after": after_order,
        "monotonicity_change": round(after_order - before_order, 2),
        "could_end_the_game": could_end_the_game(after),
        "board_after": values(after),
    }


def legal_moves(board):
    """Every direction that would change the board, with its consequences."""
    return {
        direction: result
        for direction in DIRECTIONS
        for result in [outcome(board, direction)]
        if result is not None
    }


def describe(direction, result):
    """One line of evidence for a direction, used as its Choice criterion.

    The criterion is the text the decision is actually made against, so it
    carries the same facts as the JSON rather than a summary of them.
    """
    parts = []
    if result["tiles_merged"]:
        parts.append(
            f"merges {result['tiles_merged']} pair(s) for {result['points_gained']} points"
        )
    else:
        parts.append("merges nothing")
    parts.append(f"leaves {result['empty_cells_after']} empty cells")
    parts.append(
        "keeps the largest tile in a corner"
        if result["largest_tile_stays_in_corner"]
        else "moves the largest tile out of a corner"
    )
    parts.append(f"leaves {len(result['moves_available_after'])} legal direction(s)")
    parts.append(f"sets up {result['merges_available_after']} mergeable pair(s)")
    parts.append(
        f"tile ordering {result['monotonicity_after']:.2f} "
        f"({result['monotonicity_change']:+.2f})"
    )
    line = f"Move {direction}: " + ", ".join(parts) + "."
    if result["could_end_the_game"]:
        line += " An unlucky spawn after this move would end the game."
    return line


def build_state(board, moves_played=0, recent_moves=()):
    """The JSON state describing this position and what each move would do."""
    grid = values(board)
    options = legal_moves(board)
    return {
        "game": "2048",
        "goal": "Survive as long as possible and build the largest tile.",
        "board": {
            "grid": grid,
            "note": "grid[row][column], row 0 is the top. null is an empty cell.",
            "score": board.score,
            "empty_cells": empty_count(board),
            "largest_tile": largest_tile(board),
            "largest_tile_cell": largest_tile_cell(board),
            "largest_tile_in_corner": max_tile_in_corner(board),
            "merges_available": merges_available(board),
            "monotonicity": monotonicity(board),
            "monotonicity_note": (
                "0 to 1: how well the tiles step down from the corner nearest the "
                "largest tile. 1 is a clean staircase, which is what keeps merges "
                "lining up."
            ),
        },
        "history": {
            "moves_played": moves_played,
            "recent_moves": list(recent_moves)[-RECENT_MOVES:],
            "note": (
                "Most recent last. A direction played over and over without the "
                "board improving is a game going round in circles."
            ),
        },
        "available_moves": options,
        "available_moves_note": (
            "Only moves the engine would accept are listed. Every figure is the "
            "position this move produces, before the random tile that spawns "
            "after it; could_end_the_game is the risk that spawn then carries."
        ),
    }


def move_criteria(state):
    """The Choice criteria: only the moves that would actually change the board.

    Offering an illegal direction would mean the model could waste a turn on a
    move the engine is going to refuse, so it is left out entirely.
    """
    return {
        direction: describe(direction, result)
        for direction, result in state["available_moves"].items()
    }
