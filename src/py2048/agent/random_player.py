"""
The random player: it picks a legal move and nothing more.

Worth having for two reasons. It is the floor every other player is measured
against - a search that cannot beat random is not searching - and it is the
smallest thing that meets the player contract, so it is what to copy when
adding one.

Its probabilities are not a flourish. A uniform choice over the legal moves is
genuinely this player's distribution, which is why it can be reported as one.
"""

import random

from .board import available_directions
from .contract import crowding_risk, decision


class RandomPlayer:
    """Picks uniformly from the legal moves."""

    def __init__(self, rng=None):
        # Injectable so a specification can seed it. Defaulting to the module
        # rather than a private Random means `random.seed` in a scenario
        # reaches this player too.
        self.rng = rng or random

    async def close(self):
        """Nothing to close. Here because every player is closed on shutdown."""

    async def choose(self, board, moves_played=0, recent_moves=()):
        legal = available_directions(board)
        if not legal:
            return None, decision(None, "fallback", reason="no legal moves")

        move = self.rng.choice(legal)
        share = round(1 / len(legal), 3)
        return move, decision(
            move, "random",
            detail=f"one of {len(legal)} legal moves, picked at random",
            probabilities={direction: share for direction in legal},
            confidence=share,
            risk=crowding_risk(board),
        )


__all__ = ["RandomPlayer"]
