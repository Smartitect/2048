"""
The board primitives a player needs, whoever it is.

Everything here is about *acting* on a board: which directions are legal, and
what a move would do to a copy. Judging a position - whether it is tidy,
crowded or one spawn from death - is each agent's own business and lives with
the agent that does the judging.

Nothing here mutates the board it is given. A player is asking about a game,
not playing it: the engine plays it.
"""

from ..engine import Board

DIRECTIONS = ("UP", "DOWN", "LEFT", "RIGHT")


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


def available_directions(board):
    """Every direction that would change this board, in a fixed order.

    The order is `DIRECTIONS`, not a preference - a player that has one says so
    itself. Fixed, though, so that a player with no preference is still
    reproducible.
    """
    return [
        direction for direction in DIRECTIONS if copy_board(board).make_move(direction)
    ]


__all__ = ["DIRECTIONS", "available_directions", "copy_board", "empty_count", "values"]
