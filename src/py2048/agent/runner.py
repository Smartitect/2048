"""
The loop that lets an AI player drive a game.

It knows nothing about HTTP: it holds a session, asks a player for a move,
applies it, and waits. The web layer starts and stops it; because every move
goes through the session, the browser sees them over the event stream it is
already listening to.

It also holds the players there are to choose from and which one has the game.
Swapping players is a property of who is playing, not of the transport, so it
lives here rather than in the web layer.
"""

import asyncio

from .player import decision

# Slow enough to watch. A decision takes anywhere from a few milliseconds to
# about the search's thinking time, so this pause is for the human on top of
# whatever the player itself takes.
DEFAULT_INTERVAL = 1.0

MIN_INTERVAL = 0.05
MAX_INTERVAL = 10.0


class AgentRunner:

    def __init__(self, session, players, interval=DEFAULT_INTERVAL):
        self.session = session
        self.players = dict(players)
        if not self.players:
            raise ValueError("an agent runner needs at least one player")
        # The first one registered has the game until someone picks another.
        self.name = next(iter(self.players))
        self.interval = interval
        self._task = None

    @property
    def running(self):
        return self._task is not None and not self._task.done()

    @property
    def player(self):
        return self.players[self.name]

    def select(self, name):
        """Hand the game to a different player. Refuses a name it does not know.

        Refusing rather than falling back matters: a typo that quietly started
        a different player would be indistinguishable, from the outside, from
        the one asked for playing badly.
        """
        if name not in self.players:
            known = ", ".join(self.players)
            raise ValueError(f"{name} is not one of {known}")
        self.name = name

    async def start(self, interval=None, player=None):
        if player is not None:
            self.select(player)
        if interval is not None:
            self.interval = max(MIN_INTERVAL, min(MAX_INTERVAL, float(interval)))
        if self.running:
            return False
        self._task = asyncio.create_task(self._play())
        return True

    async def close(self):
        """Stop, and close every player. Called when the app shuts down."""
        await self.stop()
        for player in self.players.values():
            await player.close()

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
                move, record = await self.player.choose(
                    board, self.session.moves, self.session.history
                )
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
            self.session.decision = decision(
                None, "fallback",
                reason=f"agent stopped: {type(error).__name__}: {error}",
            )
            await self.session.announce()
        else:
            # The game ended on its own. Clear the task before announcing, or
            # the browser is told the agent is still playing a dead board.
            self._task = None
            await self.session.announce()
