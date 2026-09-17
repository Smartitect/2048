# Import the pygame module
import pygame
import random
from .engine import Board

# Import pygame.locals for easier access to key coordinates
# Updated to conform to flake8 and black standards
from pygame.locals import (
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_ESCAPE,
    K_r,
    KEYDOWN,
    QUIT,
)

# The only keys that move tiles. Keeping the mapping here rather than in a
# chain of ifs inside the event loop makes it something a spec can check.
MOVE_KEYS = {
    K_UP: 'UP',
    K_DOWN: 'DOWN',
    K_LEFT: 'LEFT',
    K_RIGHT: 'RIGHT',
}


def move_for_key(key):
    """The move a key means, or None if it is not a movement key."""
    return MOVE_KEYS.get(key)

# Colours
OVERLAY = pygame.Color(238, 228, 218, 200)
TEXT_DARK = pygame.Color(119, 110, 100)
TEXT_LIGHT = pygame.Color(255, 255, 255)
BACKGROUND = pygame.Color(188, 173, 159)
EMPTY = pygame.Color(206, 192, 179)
TILE_MAX = pygame.Color(18, 91, 146)

CELL_STYLES = {
    0: {"font": TEXT_DARK, "fill": EMPTY},
    1: {"font": TEXT_DARK, "fill": pygame.Color(239, 229, 218)},
    2: {"font": TEXT_DARK, "fill": pygame.Color(238, 225, 199)},
    3: {"font": TEXT_LIGHT, "fill": pygame.Color(242, 177, 121)},
    4: {"font": TEXT_LIGHT, "fill": pygame.Color(245, 149, 99)},
    5: {"font": TEXT_LIGHT, "fill": pygame.Color(247, 127, 96)},
    6: {"font": TEXT_LIGHT, "fill": pygame.Color(246, 94, 59)},
    7: {"font": TEXT_LIGHT, "fill": pygame.Color(241, 219, 147)},
    8: {"font": TEXT_LIGHT, "fill": pygame.Color(237, 204, 97)},
    9: {"font": TEXT_LIGHT, "fill": pygame.Color(235, 193, 57)},
    10: {"font": TEXT_LIGHT, "fill": pygame.Color(231, 181, 23)},
    11: {"font": TEXT_DARK, "fill": pygame.Color(192, 154, 16)},
    12: {"font": TEXT_LIGHT, "fill": pygame.Color(94, 218, 146)},
    13: {"font": TEXT_LIGHT, "fill": pygame.Color(37, 187, 100)},
    14: {"font": TEXT_LIGHT, "fill": pygame.Color(35, 140, 81)},
    15: {"font": TEXT_LIGHT, "fill": pygame.Color(113, 180, 213)},
    16: {"font": TEXT_LIGHT, "fill": pygame.Color(25, 130, 205)},
}

# Define constants for the screen width and height
BORDER_WIDTH = 10
TILE_SIZE = 100
NUMBER_OF_ROWS = NUMBER_OF_COLUMNS = 4
SCREEN_WIDTH = SCREEN_HEIGHT = ((NUMBER_OF_ROWS + 1) * BORDER_WIDTH) + (NUMBER_OF_ROWS * TILE_SIZE)

FONT_SIZE = 24



class Tile(pygame.sprite.Sprite):

    def __init__(self, x, y, value=None):
        """A sprite for the board cell at (x, y), following the board's own
        convention: x is the column, y is the row."""
        super(Tile, self).__init__()
        self.font = pygame.font.Font(pygame.font.get_default_font(), FONT_SIZE)
        self.x_pos = BORDER_WIDTH + (x * (BORDER_WIDTH + TILE_SIZE))
        self.y_pos = BORDER_WIDTH + (y * (BORDER_WIDTH + TILE_SIZE))
        self.surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.value = value
        self.update(value)
    
    def update(self, value):
        self.change_fill(value)
        self.change_text(value)
        self.value = value

    def change_text(self, value):
        if value:
            if value in CELL_STYLES:
                text_colour = CELL_STYLES[value]["font"]
            else:
                text_colour = TEXT_LIGHT
            text_surface = self.font.render(str(2 ** value), True, text_colour, None)
            text_rectangle = text_surface.get_rect(center=(TILE_SIZE/2, TILE_SIZE/2))
            self.surface.blit(text_surface, text_rectangle)

    def change_fill(self, value):
        if value:
            if value in CELL_STYLES:
                fill_colour = CELL_STYLES[value]["fill"]
            else:
                fill_colour = TILE_MAX
        else:
            fill_colour = EMPTY
        self.surface.fill(fill_colour)


class Game:

    def __init__(self):
        # Set up group to hold tile sprite objects
        self.all_tiles = pygame.sprite.Group()
        # The size is determined by the constant SCREEN_WIDTH and SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen.fill(BACKGROUND)
        # Initial the 16 tiles as sprites
        self.tiles = self.initialise_tiles()
        self.draw_tiles()

    def initialise_tiles(self):
        """Build the sprite grid as tiles[y][x], matching Board.grid."""
        tiles = []
        for y in range(0, NUMBER_OF_ROWS):
            row_of_tiles = []
            for x in range(0, NUMBER_OF_COLUMNS):
                tile = Tile(x, y)
                row_of_tiles.append(tile)
                self.all_tiles.add(tile)
            tiles.append(row_of_tiles)
        return tiles

    def update_tiles(self, tile_values):
        for y in range(0, NUMBER_OF_ROWS):
            for x in range(0, NUMBER_OF_COLUMNS):
                self.tiles[y][x].update(tile_values[y][x])

    def draw_tiles(self):
        for tile in self.all_tiles:
            self.screen.blit(tile.surface, (tile.x_pos, tile.y_pos))

    def draw_game_over(self, score, move_counter):
        """Dim the board and say so, rather than leaving a dead board live."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY)
        self.screen.blit(overlay, (0, 0))

        heading = pygame.font.Font(pygame.font.get_default_font(), FONT_SIZE * 2)
        detail = pygame.font.Font(pygame.font.get_default_font(), FONT_SIZE)
        lines = [
            (heading, "GAME OVER", -40),
            (detail, "Score {} in {} moves".format(score, move_counter), 10),
            (detail, "R to restart, Esc to quit", 45),
        ]
        for font, text, offset in lines:
            surface = font.render(text, True, TEXT_DARK)
            rectangle = surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + offset))
            self.screen.blit(surface, rectangle)
    
    @staticmethod
    def convert_grid(grid):
        """Read Board.grid as plain values, cell for cell.

        Both sides are grid[y][x] now, so there is nothing to transpose: this
        only unwraps the Tile objects into the values the sprites display.
        """
        return [
            [None if tile is None else tile.get_value() for tile in row]
            for row in grid
        ]


def new_game():
    """A fresh board with its two starting tiles."""
    board = Board()
    board.add_random_tiles(2)
    return board


def render(game, board, move_counter, game_over):
    game.update_tiles(Game.convert_grid(board.grid))
    game.draw_tiles()
    if game_over:
        game.draw_game_over(board.score, move_counter)
    pygame.display.flip()


def main():

    # Initialize pygame
    pygame.init()
    game = Game()
    board = new_game()

    move_counter = 0
    game_over = not board.can_move()
    render(game, board, move_counter, game_over)

    # Variable to keep the main loop running
    running = True

    # Main loop
    while running:
        # Look at every event in the queue
        for event in pygame.event.get():
            # Did the user click the window close button? If so, stop the loop.
            if event.type == QUIT:
                running = False

            # Did the user hit a key?
            elif event.type == KEYDOWN:
                # Was it the Escape key? If so, stop the loop.
                if event.key == K_ESCAPE:
                    running = False

                elif event.key == K_r:
                    board = new_game()
                    move_counter = 0
                    game_over = not board.can_move()
                    render(game, board, move_counter, game_over)

                elif not game_over:
                    # A dead board takes no more moves: without this it would
                    # keep accepting keys that silently do nothing.
                    move = move_for_key(event.key)
                    if move is not None and board.make_move(move):
                        board.add_random_tiles(1)
                        move_counter = move_counter + 1
                        game_over = not board.can_move()
                        render(game, board, move_counter, game_over)

if __name__ == "__main__":
    main()
