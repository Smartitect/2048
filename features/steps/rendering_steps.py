"""
Step definitions for the pygame rendering specification.

The point of these steps is orientation: a transposed render is still a
plausible-looking 2048 board, so the only way to catch one is to assert where
each value lands on screen against where the board says it is.

SDL runs on the dummy driver, so this works with no display attached.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402  - the driver must be chosen before pygame starts

from behave import then

from py2048.pygame_ui import BORDER_WIDTH, TILE_SIZE, Game, move_for_key

from board_steps import grid_from_board


def screen_position(x, y):
    """Where the tile in board cell (x, y) belongs on screen."""
    return (
        BORDER_WIDTH + (x * (BORDER_WIDTH + TILE_SIZE)),
        BORDER_WIDTH + (y * (BORDER_WIDTH + TILE_SIZE)),
    )


@then("the pygame UI draws every tile in its board position")
def step_then_render_matches_board(context):
    pygame.init()
    try:
        game = Game()
        game.update_tiles(Game.convert_grid(context.board.grid))

        drawn = {(tile.x_pos, tile.y_pos): tile.value for tile in game.all_tiles}
        assert len(drawn) == 16, f"expected 16 tile positions, got {len(drawn)}"

        grid = grid_from_board(context.board)
        mismatches = []
        for y in range(4):
            for x in range(4):
                expected = grid[y][x]
                value = drawn[screen_position(x, y)]
                actual = None if value is None else 2 ** value
                if actual != expected:
                    mismatches.append(
                        f"cell (x={x}, y={y}) holds {expected} but the screen shows {actual}"
                    )
        assert not mismatches, "\n".join(mismatches)
    finally:
        pygame.quit()


def key_constant(name):
    """The pygame key constant a spec names, e.g. UP -> K_UP, r -> K_r."""
    for candidate in (f"K_{name}", f"K_{name.lower()}"):
        if hasattr(pygame, candidate):
            return getattr(pygame, candidate)
    raise ValueError(f"pygame has no key called {name}")


def screen_bytes(board, game_over):
    """Render a board headless and return its pixels."""
    pygame.init()
    try:
        game = Game()
        game.update_tiles(Game.convert_grid(board.grid))
        game.draw_tiles()
        if game_over:
            game.draw_game_over(board.score, 0)
        return pygame.image.tostring(game.screen, "RGB")
    finally:
        pygame.quit()


@then("the {key} key means {move}")
def step_then_key_means(context, key, move):
    expected = None if move == "none" else move
    actual = move_for_key(key_constant(key))
    assert actual == expected, f"{key} mapped to {actual}, expected {expected}"


@then("the pygame UI marks the game as over")
def step_then_marks_game_over(context):
    live = screen_bytes(context.board, game_over=False)
    over = screen_bytes(context.board, game_over=True)
    assert live != over, "the game-over screen is identical to the live board"


@then("the pygame UI draws the board without an overlay")
def step_then_no_overlay(context):
    plain = screen_bytes(context.board, game_over=False)
    again = screen_bytes(context.board, game_over=False)
    assert plain == again, "rendering the same live board twice gave different screens"
