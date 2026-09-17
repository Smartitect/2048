"""
Python 2048 Game : Browser Based User Interface

The engine stays authoritative and the browser is a pure view: it captures keys,
posts them, and renders whatever state comes back. No game logic lives in
JavaScript, so there is only ever one implementation of the rules and the
specifications cover it.

State reaches the browser two ways: a snapshot at GET /api/state, and a push
over server-sent events at GET /api/events. The board only changes when the
engine says so, which is the shape SSE fits.
"""

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from ..engine import Board

STATIC = Path(__file__).parent / "static"

DIRECTIONS = ("UP", "DOWN", "LEFT", "RIGHT")

# A quiet stream still has to say something occasionally: it keeps the connection
# alive through proxies, and it means the generator is never parked forever on a
# queue it cannot be woken from.
HEARTBEAT_SECONDS = 15


class MoveRequest(BaseModel):
    direction: str


class GameSession:
    """One game, plus whoever is watching it.

    Every change broadcasts to all subscribers, so two open tabs stay in step,
    and a search driving the same session needs no extra machinery.
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._subscribers = set()
        self.new_game()

    def new_game(self):
        self.board = Board()
        self.board.add_random_tiles(2)
        self.moves = 0
        self.last_move = None

    def state(self):
        """The board as tile values: the browser never sees an exponent."""
        max_tile, max_row, max_column = self.board.get_max_tile()
        return {
            "grid": [
                [None if tile is None else tile.get_tile_value() for tile in row]
                for row in self.board.grid
            ],
            "score": self.board.score,
            "mergeCount": self.board.merge_count,
            "moves": self.moves,
            "lastMove": self.last_move,
            "gameOver": not self.board.can_move(),
            "maxTile": max_tile,
        }

    async def apply_move(self, direction):
        """Play one move. Returns the new state and whether the board changed."""
        if direction not in DIRECTIONS:
            raise ValueError(f"{direction} is not one of {', '.join(DIRECTIONS)}")
        async with self._lock:
            moved = self.board.make_move(direction)
            if moved:
                self.board.add_random_tiles(1)
                self.moves = self.moves + 1
                self.last_move = direction
            state = self.state()
        await self.broadcast(state)
        return state, moved

    async def restart(self):
        async with self._lock:
            self.new_game()
            state = self.state()
        await self.broadcast(state)
        return state

    def subscribe(self):
        queue = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue):
        self._subscribers.discard(queue)

    async def broadcast(self, state):
        for queue in list(self._subscribers):
            queue.put_nowait(state)


def create_app():
    app = FastAPI(title="py2048")
    app.state.session = GameSession()

    @app.get("/")
    async def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/api/state")
    async def get_state():
        return app.state.session.state()

    @app.post("/api/move")
    async def post_move(request: MoveRequest):
        try:
            state, moved = await app.state.session.apply_move(request.direction.upper())
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error))
        return {"moved": moved, "state": state}

    @app.post("/api/new")
    async def post_new():
        return await app.state.session.restart()

    @app.get("/api/events")
    async def events():
        """Push state to a browser until it goes away."""
        session = app.state.session
        queue = session.subscribe()

        async def stream():
            try:
                # Open with the current state, so a tab that connects late is
                # not left staring at an empty board until the next move.
                yield f"data: {json.dumps(session.state())}\n\n"
                while True:
                    try:
                        state = await asyncio.wait_for(queue.get(), HEARTBEAT_SECONDS)
                    except asyncio.TimeoutError:
                        yield ": keep-alive\n\n"
                        continue
                    yield f"data: {json.dumps(state)}\n\n"
            finally:
                session.unsubscribe(queue)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return app


app = create_app()


def run():
    """Entry point for `uv run py2048-web`."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run()
