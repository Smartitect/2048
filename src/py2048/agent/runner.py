"""
The loop that lets an AI player drive a game.

It knows nothing about HTTP: it holds a session, asks a player for a move,
applies it, and waits. The web layer starts and stops it; because every move
goes through the session, the browser sees them over the event stream it is
already listening to.
"""

import asyncio

# Slow enough to watch. A decision takes well under a second, so the pause is
# for the human, not the model.
DEFAULT_INTERVAL = 1.0

MIN_INTERVAL = 0.05
MAX_INTERVAL = 10.0


class AgentRunner:

    def __init__(self, session, player, interval=DEFAULT_INTERVAL):
        self.session = session
        self.player = player
        self.interval = interval
        self._task = None

    @property
    def running(self):
        return self._task is not None and not self._task.done()

    async def start(self, interval=None):
        if interval is not None:
            self.interval = max(MIN_INTERVAL, min(MAX_INTERVAL, float(interval)))
        if self.running:
            return False
        self._task = asyncio.create_task(self._play())
        return True

    async def stop(self):
        if not self.running:
            return False
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        await self.session.announce()
        return True

    async def _play(self):
        try:
            while True:
                board = self.session.board
                if not board.can_move():
                    break
                move, record = await self.player.choose(board, self.session.moves)
                if move is None:
                    break
                await self.session.apply_move(move, record)
                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            self._task = None
            raise
        except Exception as error:
            # A loop that dies quietly looks like a loop that was never asked to
            # play, so it says what happened.
            self._task = None
            self.session.decision = {
                "move": None,
                "source": "fallback",
                "reason": f"agent stopped: {type(error).__name__}: {error}",
                "probabilities": None,
                "confidence": None,
                "risk": None,
                "latencyMs": None,
            }
            await self.session.announce()
        else:
            # The game ended on its own. Clear the task before announcing, or
            # the browser is told the agent is still playing a dead board.
            self._task = None
            await self.session.announce()
