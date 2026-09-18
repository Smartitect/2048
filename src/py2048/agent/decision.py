"""
The shape a player's answer takes, shared by every AI player.

A decision says what was played and who decided it. Two things follow from the
rule that a fallback is never silent: `source` names whoever actually chose,
which is not always the player that was asked, and `reason` says why when it
was not.

`reason` is for a fallback and reads as one on screen. A player with something
to say about a decision it did make - how hard it looked, how sure it is - puts
it in `detail`.
"""

# Comfortable room. Below this the board starts closing in, and at one free
# cell it is as bad as the scale goes.
COMFORTABLE_EMPTY_CELLS = 8

MAX_RISK = 2.0


def decision(move, source, reason=None, detail=None, probabilities=None,
             confidence=None, risk=None, latency_ms=None):
    """One decision, in the shape the browser renders."""
    return {
        "move": move,
        "source": source,               # "jev", "mcts", "fallback" or "human"
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
