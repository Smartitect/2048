"""
Turning a Board into the JSON state an AI player is asked about.

The engine already knows what each move would do, so it says so rather than
leaving the model to simulate 2048 in its head: the code does the arithmetic,
the model does the judging. Everything here is derived by playing the move on a
copy, so the facts cannot drift from the rules.

Nothing in this module talks to a model, which is what makes it easy to check.
"""

from ..engine import Board

DIRECTIONS = ("UP", "DOWN", "LEFT", "RIGHT")

CORNERS = ((0, 0), (3, 0), (0, 3), (3, 3))


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


def max_tile_in_corner(board):
    grid = values(board)
    largest = max((cell for row in grid for cell in row if cell), default=0)
    return any(grid[y][x] == largest for x, y in CORNERS)


def outcome(board, direction):
    """What this direction would do, played out on a copy.

    The spawn that follows a real move is left out: it is random, so it is not
    a consequence of choosing this direction and has no business being stated
    as one.
    """
    after = copy_board(board)
    moved = after.make_move(direction)
    if not moved:
        return None
    return {
        "legal": True,
        "points_gained": after.score - board.score,
        "tiles_merged": after.merge_count - board.merge_count,
        "empty_cells_after": empty_count(after),
        "empty_cells_gained": empty_count(after) - empty_count(board),
        "largest_tile_stays_in_corner": max_tile_in_corner(after),
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
    """One line of evidence for a direction, used as its Choice criterion."""
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
    return f"Move {direction}: " + ", ".join(parts) + "."


def build_state(board, moves_played=0):
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
            "moves_played": moves_played,
            "empty_cells": empty_count(board),
            "largest_tile": max((cell for row in grid for cell in row if cell), default=0),
            "largest_tile_in_corner": max_tile_in_corner(board),
        },
        "available_moves": options,
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
