"""
What a player is, and the shape of the answer it gives.

A player is anything with these two methods:

```python
async def choose(self, board, moves_played=0, recent_moves=()):
    '''Return (direction, decision) - or (None, decision) if there is no move.'''

async def close(self):
    '''Release anything held open. Called once, when the app shuts down.'''
```

That is the whole contract - hence the name of this file. There is no base
class to inherit: a player that answers `choose` is a player, and `AgentRunner`
cannot tell one from another. Each agent's own implementation is the `player.py`
inside its own folder, or a `*_player.py` module when one is all it needs.
Three rules go with it, and they are the reason a player is trusted with a
game:

- **The engine stays authoritative.** A player names a direction. What that
  does to the board is the engine's business, and the engine may still refuse.
- **Only legal moves are returned.** A player that cannot find one returns
  None rather than a direction the engine will throw away.
- **A fallback is never silent.** When something other than the player decided
  - no key, an error, a position not worth thinking about - `source` says so
  and `reason` says why.

`moves_played` and `recent_moves` are offered to every player because a player
that is asked one position at a time has no other way to see a game going round
in circles. A player that does not need them ignores them.
"""

# Comfortable room. Below this the board starts closing in, and at one free
# cell it is as bad as the scale goes.
COMFORTABLE_EMPTY_CELLS = 8

MAX_RISK = 2.0


def decision(move, source, reason=None, detail=None, probabilities=None,
             confidence=None, risk=None, latency_ms=None):
    """One decision, in the shape the browser renders.

    `reason` is for a fallback and reads as one on screen. A player with
    something to say about a decision it *did* make - how hard it looked, what
    rule it followed - puts it in `detail`.
    """
    return {
        "move": move,
        "source": source,               # the player's name, or "fallback"/"human"
        "reason": reason,               # why it fell back, when it did
        "detail": detail,               # what the player wants to say about it
        "probabilities": probabilities,
        "confidence": confidence,
        "risk": risk,
        "latencyMs": latency_ms,
    }


def crowding_risk(board):
    """How much trouble the board is in, on the 0-2 scale the browser shows.

    Jev answers this question itself, as a `Score`. A local player has no one
    to ask, so it is worked out here from the room left - which is the part of
    the question a player can answer without judgement.
    """
    empty = len(board.get_empty_cells())
    risk = (COMFORTABLE_EMPTY_CELLS - empty) / (COMFORTABLE_EMPTY_CELLS - 1) * MAX_RISK
    return round(min(MAX_RISK, max(0.0, risk)), 2)


__all__ = ["decision", "crowding_risk"]
