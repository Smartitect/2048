"""
The rules player: keep pushing into one corner, and only break that when forced.

It plays the first direction on a fixed list that the engine will accept. The
default list is UP then RIGHT, so the tiles pile into the top-right corner, and
DOWN then LEFT when neither of those is legal.

This is the oldest advice in 2048 and it plays a respectable game, because the
two directions that hold a corner also keep the big tiles adjacent, which is
what keeps merges lining up. It fails the way every fixed policy fails: when
the preferred pair is exhausted it has to break its own structure, and it has
no way of choosing which break hurts least.

The same order is what an AI player falls back to when it cannot be asked, so
the fallback has a name, a corner and scenarios of its own rather than being a
tuple buried in a client.
"""

from .board import available_directions
from .contract import crowding_risk, decision

# Push into the top-right: UP and RIGHT hold that corner, DOWN and LEFT break
# it. Listed worst-last, so "the first legal one" is also "the least damaging".
TOP_RIGHT = ("UP", "RIGHT", "DOWN", "LEFT")

# The mirror image, for a game built into the bottom left.
BOTTOM_LEFT = ("LEFT", "DOWN", "UP", "RIGHT")


def preferred_move(legal, order=TOP_RIGHT):
    """The first direction in `order` that is legal, or None.

    Takes the legal moves rather than the board, so a player that has already
    worked them out does not work them out twice.
    """
    for direction in order:
        if direction in legal:
            return direction
    return None


class RulesPlayer:
    """Plays the first legal direction on its list, every time.

    Deterministic: the same board always gets the same move, which makes it a
    useful control when something else in the system starts behaving oddly.
    """

    def __init__(self, order=TOP_RIGHT):
        self.order = tuple(order)

    async def close(self):
        """Nothing to close. Here because every player is closed on shutdown."""

    async def choose(self, board, moves_played=0, recent_moves=()):
        legal = available_directions(board)
        move = preferred_move(legal, self.order)
        if move is None:
            return None, decision(None, "fallback", reason="no legal moves")

        # No probabilities: a rule that always answers the same way has no
        # distribution to report, and inventing one would put a bar chart on
        # screen that says nothing.
        return move, decision(
            move, "rules",
            detail=" → ".join(self.order) + "; the first legal one wins",
            risk=crowding_risk(board),
        )


__all__ = ["RulesPlayer", "preferred_move", "TOP_RIGHT", "BOTTOM_LEFT"]
