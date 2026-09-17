"""
Step definitions for the py2048 specifications.

Board state is written in the feature files as tile *values* (2, 4, 8), which is
what a player sees, while the engine stores exponents. The conversion lives here
so the specifications never mention exponents.

A four-row Gherkin table has no header, so behave reads its first row as the
headings. `grid_from_table` puts that row back where it belongs, which is what
lets a scenario show the grid exactly as it appears on screen.
"""

import random

from behave import given, when, then

from py2048 import Board, Tile

GRID_SIZE = 4

# A cell is empty when it is blank; "." is accepted for the inline line
# notation, where a blank between quotes would be invisible.
EMPTY_CELL = {"", "."}

DIRECTIONS = ("UP", "DOWN", "LEFT", "RIGHT")


def parse_cell(text):
    """Turn one table cell into a tile value, or None when it is empty."""
    text = text.strip()
    if text in EMPTY_CELL:
        return None
    value = int(text)
    if value < 2 or value & (value - 1):
        raise ValueError(f"{value} is not a power of two, so no tile can hold it")
    return value


def grid_from_table(table):
    """Read a headerless four-by-four table as a grid of tile values."""
    rows = [list(table.headings)] + [list(row.cells) for row in table]
    if len(rows) != GRID_SIZE or any(len(row) != GRID_SIZE for row in rows):
        raise ValueError(f"a board table must be {GRID_SIZE}x{GRID_SIZE}, got {rows}")
    return [[parse_cell(cell) for cell in row] for row in rows]


def board_from_grid(grid):
    """Build a Board from tile values, converting each to the stored exponent."""
    return Board(initial_state=[
        [None if value is None else value.bit_length() - 1 for value in row]
        for row in grid
    ])


def grid_from_board(board):
    """Read a Board back out as tile values."""
    return [
        [None if exponent is None else 2 ** exponent for exponent in row]
        for row in board.export_state()
    ]


def render(grid):
    """Render a grid the way the feature files write it, for failure output."""
    return [
        "|" + "|".join(f"{'' if v is None else v: ^6}" for v in row) + "|"
        for row in grid
    ]


def assert_grids_equal(expected, actual):
    """Compare two grids, showing them side by side when they differ."""
    if expected == actual:
        return
    lines = ["", f"{'expected': ^27}   {'actual': ^27}"]
    for exp_row, act_row, exp, act in zip(render(expected), render(actual), expected, actual):
        lines.append(f"{exp_row}   {act_row}   {'' if exp == act else '<-- differs'}")
    raise AssertionError("\n".join(lines))


def line_coordinates(direction):
    """
    The coordinates of one line, ordered from the edge the move pushes toward.

    This is what lets a single scenario state a merge rule once and check it in
    all four directions: index 0 is always the destination edge, so "2 2 2 2"
    means the same thing whichever way the board is being tilted.
    """
    if direction == "LEFT":
        return [(x, 0) for x in range(GRID_SIZE)]
    if direction == "RIGHT":
        return [(GRID_SIZE - 1 - x, 0) for x in range(GRID_SIZE)]
    if direction == "UP":
        return [(0, y) for y in range(GRID_SIZE)]
    if direction == "DOWN":
        return [(0, GRID_SIZE - 1 - y) for y in range(GRID_SIZE)]
    raise ValueError(f"{direction} is not one of {DIRECTIONS}")


def parse_line(text):
    return [parse_cell(cell) for cell in text.split()]


@given("a board")
def step_given_a_board(context):
    context.board = board_from_grid(grid_from_table(context.table))
    context.starting_grid = grid_from_board(context.board)


@given("an empty board")
def step_given_an_empty_board(context):
    context.board = Board()
    context.starting_grid = grid_from_board(context.board)


@given('the line facing {direction} is "{line}"')
def step_given_line(context, direction, line):
    values = parse_line(line)
    coordinates = line_coordinates(direction)
    if len(values) != len(coordinates):
        raise ValueError(f"a line needs {GRID_SIZE} cells, got {line!r}")
    for (x, y), value in zip(coordinates, values):
        context.board.grid[y][x] = None if value is None else Tile(value.bit_length() - 1)
    context.starting_grid = grid_from_board(context.board)


@given("the random seed is {seed:d}")
def step_given_seed(context, seed):
    context.seed = seed
    random.seed(seed)


@when("the player moves {direction}")
def step_when_move(context, direction):
    context.move_result = context.board.make_move(direction)


@when("{count:d} random tile is added")
@when("{count:d} random tiles are added")
def step_when_add_tiles(context, count):
    context.added_count = count
    context.grid_before_add = grid_from_board(context.board)
    context.add_result = context.board.add_random_tiles(count)


@then("the board is")
def step_then_board_is(context):
    assert_grids_equal(grid_from_table(context.table), grid_from_board(context.board))


@then("the board is unchanged")
def step_then_board_unchanged(context):
    assert_grids_equal(context.starting_grid, grid_from_board(context.board))


@then('the line facing {direction} is "{line}"')
def step_then_line(context, direction, line):
    grid = grid_from_board(context.board)
    actual = [grid[y][x] for x, y in line_coordinates(direction)]
    expected = parse_line(line)
    assert actual == expected, f"expected {expected}, got {actual}"


@then("the move is accepted")
def step_then_move_accepted(context):
    assert context.move_result is True, "the move reported no change to the board"


@then("the move is rejected")
def step_then_move_rejected(context):
    assert context.move_result is False, "the move reported a change to the board"


@then("the score is {score:d}")
def step_then_score(context, score):
    assert context.board.score == score, f"expected score {score}, got {context.board.score}"


@then("the merge count is {count:d}")
def step_then_merge_count(context, count):
    actual = context.board.merge_count
    assert actual == count, f"expected merge count {count}, got {actual}"


@then("the board holds {count:d} tiles")
def step_then_tile_count(context, count):
    actual = sum(cell is not None for row in grid_from_board(context.board) for cell in row)
    assert actual == count, f"expected {count} tiles, got {actual}"


@then("every tile is a 2 or a 4")
def step_then_tiles_are_spawnable(context):
    values = [cell for row in grid_from_board(context.board) for cell in row if cell]
    assert all(value in (2, 4) for value in values), f"unexpected spawn values: {values}"


@then("all the tiles were placed")
def step_then_all_placed(context):
    assert context.add_result is True, "add_random_tiles reported that it ran out of room"


@then("not all the tiles were placed")
def step_then_not_all_placed(context):
    assert context.add_result is False, "add_random_tiles reported that they all fitted"


@then("re-running that with the same seed gives the same board")
def step_then_seed_is_deterministic(context):
    """
    Replay the same spawn from the same starting board and seed.

    Comparing a replay rather than hard-coded coordinates keeps the scenario
    honest without pinning it to the internals of random.sample.
    """
    replay = board_from_grid(context.grid_before_add)
    random.seed(context.seed)
    replay.add_random_tiles(context.added_count)
    assert_grids_equal(grid_from_board(replay), grid_from_board(context.board))


@then("a move is available")
def step_then_move_available(context):
    assert context.board.can_move() is True, "can_move() says the game is over"


@then("no moves are available")
def step_then_no_moves_available(context):
    assert context.board.can_move() is False, "can_move() says a move is still possible"


@then("that verdict matches trying every direction")
def step_then_verdict_matches(context):
    """
    Check can_move() against what the moves actually do.

    Each direction is tried on its own copy of the board, so this compares the
    verdict with real behaviour rather than with a second implementation of the
    same rule.
    """
    grid = grid_from_board(context.board)
    moved = {
        direction: board_from_grid(grid).make_move(direction)
        for direction in DIRECTIONS
    }
    assert context.board.can_move() == any(moved.values()), (
        f"can_move() said {context.board.can_move()}, but the moves report {moved}"
    )
