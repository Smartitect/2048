"""
The search, wearing the player contract.

Everything specific to the algorithm is in `search.py`. This is the part
that knows about decisions, fallbacks and the event loop.
"""

import asyncio
import time

from ..board import available_directions
from ..contract import crowding_risk, decision
from .search import Settings, flat_search, search


class MctsPlayer:
    """Picks a move by searching, and says how hard it looked.

    The same interface as `JevPlayer`, so the runner and the browser cannot
    tell them apart. The search is CPU-bound and takes about as long as it is
    given, so it runs in a worker thread: on the event loop it would stall the
    event stream every single move.
    """

    def __init__(self, settings=None, strategy="tree"):
        self.settings = settings or Settings()
        self.strategy = strategy

    async def close(self):
        """Nothing to close. Here because every player is closed on shutdown."""

    async def choose(self, board, moves_played=0, recent_moves=()):
        """Pick the next move, and say who picked it.

        `moves_played` and `recent_moves` are part of the interface and are not
        used: the search reads the position, and the position is all a search
        needs.
        """
        legal = available_directions(board)
        if not legal:
            return None, decision(None, "fallback", reason="no legal moves")
        if len(legal) == 1:
            # Nothing to decide, and searching would spend half a second
            # confirming the only move on offer.
            return legal[0], decision(
                legal[0], "fallback", reason="only one legal move",
                risk=crowding_risk(board),
            )

        started = time.perf_counter()
        result = await asyncio.to_thread(self._search, board)
        latency_ms = round((time.perf_counter() - started) * 1000)

        if result.move is None:
            # The board was legal a moment ago, so this means it changed under
            # the search rather than that there is nothing to play.
            return legal[0], decision(
                legal[0], "fallback", reason="the search found no move",
                latency_ms=latency_ms, risk=crowding_risk(board),
            )

        return result.move, decision(
            result.move, "mcts",
            detail=result.summary(),
            probabilities=result.shares,
            confidence=round(result.confidence, 3),
            risk=crowding_risk(board),
            latency_ms=latency_ms,
        )

    def _search(self, board):
        if self.strategy == "flat":
            return flat_search(board, self.settings)
        return search(board, self.settings)


__all__ = ["MctsPlayer"]
