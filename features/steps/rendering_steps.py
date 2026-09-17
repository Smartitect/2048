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

from py2048.pygame_ui import BORDER_WIDTH, TILE_SIZE, Game

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
