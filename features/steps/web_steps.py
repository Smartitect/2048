"""
Step definitions for the browser front-end's API.

FastAPI's TestClient drives the app in-process, so these run with no port to
bind and no server to start. The board can be set directly on the session
because the engine is authoritative: what the browser sees is whatever the
engine holds.
"""

import json
import threading
import time

import httpx
import uvicorn
from behave import given, when, then
from fastapi.testclient import TestClient

from py2048.web.app import create_app

from board_steps import assert_grids_equal, board_from_grid, grid_from_table


def start(context):
    context.client = TestClient(create_app())
    context.response = None
    return context.client


def web_state(context):
    response = context.client.get("/api/state")
    assert response.status_code == 200, f"GET /api/state returned {response.status_code}"
    return response.json()


@given("a running web game")
def step_given_web_game(context):
    start(context)


@given("a running web game with the board")
def step_given_web_game_with_board(context):
    client = start(context)
    client.app.state.session.board = board_from_grid(grid_from_table(context.table))


@when("{direction} is posted")
def step_when_direction_posted(context, direction):
    context.response = context.client.post("/api/move", json={"direction": direction})


@when("a new game is requested")
def step_when_new_game(context):
    context.response = context.client.post("/api/new")


@then("the response says the board changed")
def step_then_board_changed(context):
    assert context.response.json()["moved"] is True, "the API reported no change"


@then("the response says the board did not change")
def step_then_board_unchanged_api(context):
    assert context.response.json()["moved"] is False, "the API reported a change"


@then("the request is rejected")
def step_then_rejected(context):
    assert context.response.status_code == 422, (
        f"expected 422, got {context.response.status_code}"
    )


@then("the web state holds {count:d} tiles")
def step_then_web_tile_count(context, count):
    grid = web_state(context)["grid"]
    actual = sum(cell is not None for row in grid for cell in row)
    assert actual == count, f"expected {count} tiles, got {actual}"


@then("the web state reports {moves:d} moves")
def step_then_web_moves(context, moves):
    actual = web_state(context)["moves"]
    assert actual == moves, f"expected {moves} moves, got {actual}"


@then("the web state reports score {score:d}")
def step_then_web_score(context, score):
    actual = web_state(context)["score"]
    assert actual == score, f"expected score {score}, got {actual}"


@then("the web state reports the game is over")
def step_then_web_game_over(context):
    assert web_state(context)["gameOver"] is True, "the API says the game continues"


@then("the web state reports the game is not over")
def step_then_web_game_not_over(context):
    assert web_state(context)["gameOver"] is False, "the API says the game is over"


@then("the web state is")
def step_then_web_state_is(context):
    assert_grids_equal(grid_from_table(context.table), web_state(context)["grid"])


@then("the page is served")
def step_then_page_served(context):
    response = context.client.get("/")
    assert response.status_code == 200, f"GET / returned {response.status_code}"
    assert "<title>py2048</title>" in response.text, "that does not look like the page"


@given("a web server is running")
def step_given_real_server(context):
    """
    Start a real uvicorn server on a free port.

    The event stream is the architectural decision this feature turned on, so it
    is worth exercising over a real socket: an in-process test client cannot
    tear down an endless stream, which is exactly what SSE is.
    """
    config = uvicorn.Config(create_app(), host="127.0.0.1", port=0, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    assert server.started, "the web server did not start"

    context.server = server
    context.server_thread = thread
    context.base_url = f"http://127.0.0.1:{server.servers[0].sockets[0].getsockname()[1]}"


@then("a listening browser is sent the board, and every move that follows")
def step_then_stream_pushes(context):
    def next_event(lines):
        for line in lines:
            if line.startswith("data: "):
                return json.loads(line[len("data: "):])
        raise AssertionError("the event stream ended without sending anything")

    with httpx.Client(base_url=context.base_url, timeout=10) as client:
        with client.stream("GET", "/api/events") as stream:
            assert stream.headers["content-type"].startswith("text/event-stream")
            lines = stream.iter_lines()

            # The stream opens with the current state, so a tab that connects
            # late is not left staring at a blank board.
            opening = next_event(lines)
            snapshot = client.get("/api/state").json()
            assert opening["grid"] == snapshot["grid"], "the opening push is not the current board"

            # A move made elsewhere reaches this listener without it asking.
            client.post("/api/move", json={"direction": "LEFT"})
            pushed = next_event(lines)
            assert pushed["grid"] == client.get("/api/state").json()["grid"], (
                "the pushed board does not match the server's board"
            )

            client.post("/api/new")
            restarted = next_event(lines)
            assert restarted["moves"] == 0, f"restart pushed {restarted['moves']} moves"
