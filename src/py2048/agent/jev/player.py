"""
The AI player: TypeSafe AI's Jev picks the move.

Jev is a System One model - it answers typed questions about a state and
returns a decision, a probability distribution and a confidence, rather than
generating text to be parsed. "Which of these moves?" is its Choice primitive,
so the board goes over as JSON and the answer comes back as one of the
directions that were offered.

Two rules hold throughout:

- Only legal moves are offered, so an illegal answer is unrepresentable.
- A fallback is never silent. No key, an API error, or a confidence below the
  threshold falls back to a local policy and says so, so what is on screen is
  never mistaken for the model's judgement.
"""

import os
import time

from typesafe_sdk import AsyncTypeSafeClient, Choice, RetryPolicy, Score, TypeSafeError

from ..board import DIRECTIONS
from ..player import decision
from ..rules_player import TOP_RIGHT, preferred_move
from . import transcript
from .state import build_state, move_criteria

MODEL = "jev-latest"

# Below this, the model is telling us it cannot separate the options, so the
# local policy decides instead and the UI says so.
CONFIDENCE_THRESHOLD = 0.15

MOVE_INSTRUCTIONS = (
    "Which move gives the best position in 2048? Keep the largest tile in its "
    "corner and the tiles ordered so they step down from it, keep empty cells "
    "available, and prefer a move that sets up merges for the turn after. Avoid "
    "moves that leave few legal directions, that an unlucky spawn could end the "
    "game, and that repeat what the recent moves have already tried."
)

RISK_INSTRUCTIONS = "How much trouble is this board in?"

RISK_LEVELS = [
    "Plenty of room and the big tiles are organised",
    "Getting crowded, but there are still good moves",
    "Nearly full, one bad move from being stuck",
]

# When Jev cannot be asked or cannot decide, the rules player decides instead -
# the same corner policy, with the same name and the same scenarios, rather
# than a second copy of it buried here.
FALLBACK_ORDER = TOP_RIGHT


def api_key():
    """The key, or None. Read here so a key added later is picked up."""
    return os.environ.get("TYPESAFE_API_KEY") or None


def fallback_move(state):
    """A local policy, used when the model cannot be asked or cannot decide."""
    options = state["available_moves"]
    return preferred_move(options, FALLBACK_ORDER)


class JevPlayer:
    """Asks Jev for one move at a time.

    The client is made once and reused: a new HTTPS connection per move would
    cost more than the decision does.
    """

    def __init__(self, client=None, model=MODEL, threshold=CONFIDENCE_THRESHOLD):
        self._client = client
        self._owns_client = client is None
        self.model = model
        self.threshold = threshold

    async def client(self):
        if self._client is None:
            key = api_key()
            if key is None:
                return None
            self._client = AsyncTypeSafeClient(
                api_key=key,
                model=self.model,
                # 429 and 529 are the documented "come back later" codes, and a
                # game loop can afford to wait a moment.
                retry=RetryPolicy(max_retries=2, backoff_initial=0.5),
                timeout=20.0,
            )
        return self._client

    async def close(self):
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

    async def choose(self, board, moves_played=0, recent_moves=()):
        """Pick the next move, and say who picked it.

        `recent_moves` is the game's own history: each call is otherwise
        stateless, so without it the model cannot see a game going round in
        circles.
        """
        state = build_state(board, moves_played, recent_moves)
        criteria = move_criteria(state)

        if not criteria:
            self._not_asked(moves_played, "no legal moves")
            return None, decision(None, "fallback", reason="no legal moves")

        if len(criteria) == 1:
            # Nothing to decide: asking would spend a call to be told the only
            # move on offer.
            only = next(iter(criteria))
            self._not_asked(moves_played, "only one legal move")
            return only, decision(only, "fallback", reason="only one legal move")

        client = await self.client()
        if client is None:
            move = fallback_move(state)
            self._not_asked(moves_played, "no TYPESAFE_API_KEY set")
            return move, decision(move, "fallback", reason="no TYPESAFE_API_KEY set")

        sent = {
            "state": state,
            "questions": transcript.questions_sent(
                MOVE_INSTRUCTIONS, criteria, RISK_INSTRUCTIONS, RISK_LEVELS
            ),
        } if transcript.enabled() else None

        started = time.perf_counter()
        try:
            response = await client.system_one(
                state=state,
                questions={
                    "move": Choice(instructions=MOVE_INSTRUCTIONS, criteria=criteria),
                    # Free: every question in a call is evaluated in parallel,
                    # and it gives the dashboard something to show.
                    "risk": Score(instructions=RISK_INSTRUCTIONS, criteria=RISK_LEVELS),
                },
            )
        except TypeSafeError as error:
            move = fallback_move(state)
            latency_ms = round((time.perf_counter() - started) * 1000)
            transcript.record(
                move_number=moves_played, sent=sent, received=None,
                error=f"{type(error).__name__}: {error}",
                latency_ms=latency_ms,
                outcome=f"fell back to {move}",
            )
            return move, decision(
                move, "fallback",
                reason=f"{type(error).__name__}: {error}",
                latency_ms=latency_ms,
            )

        latency_ms = round((time.perf_counter() - started) * 1000)
        answer = response.choices["move"]
        risk = response.scores["risk"].score if "risk" in response.scores else None
        received = transcript.answer_received(answer, risk) if transcript.enabled() else None

        def log(outcome):
            transcript.record(
                move_number=moves_played, sent=sent, received=received,
                latency_ms=latency_ms, outcome=outcome,
            )

        if answer.confidence is not None and answer.confidence < self.threshold:
            move = fallback_move(state)
            log(f"confidence below {self.threshold}, fell back to {move}")
            return move, decision(
                move, "fallback",
                reason=f"confidence {answer.confidence:.2f} below {self.threshold}",
                probabilities=dict(answer.probabilities),
                confidence=answer.confidence,
                risk=risk,
                latency_ms=latency_ms,
            )

        # The model can only answer with an option that was offered, and every
        # option offered was legal - but a board that changed underneath us
        # would make it stale, so it is checked rather than trusted.
        if answer.choice not in state["available_moves"]:
            move = fallback_move(state)
            log(f"{answer.choice} is not legal here, fell back to {move}")
            return move, decision(
                move, "fallback",
                reason=f"{answer.choice} is not legal on this board",
                probabilities=dict(answer.probabilities),
                confidence=answer.confidence,
                risk=risk,
                latency_ms=latency_ms,
            )

        log(f"played {answer.choice}")
        return answer.choice, decision(
            answer.choice, "jev",
            probabilities=dict(answer.probabilities),
            confidence=answer.confidence,
            risk=risk,
            latency_ms=latency_ms,
        )

    def _not_asked(self, moves_played, reason):
        """Say why nothing was sent, so silence is never ambiguous."""
        transcript.record(move_number=moves_played, sent=None, received=None,
                          outcome=f"not asked: {reason}")


__all__ = ["JevPlayer", "DIRECTIONS", "build_state", "fallback_move", "api_key"]
