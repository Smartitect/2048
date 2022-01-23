# Import the pygame module
import pygame
import random

# Import pygame.locals for easier access to key coordinates
# Updated to conform to flake8 and black standards
from pygame.locals import (
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)

# Colours
TEXT_DARK = pygame.Color(119, 110, 100)
TEXT_LIGHT = pygame.Color(255, 255, 255)
BACKGROUND = pygame.Color(188, 173, 159)

CELL_STYLES = {
    0: {"font": TEXT_DARK, "fill": pygame.Color(206, 192, 179)},
    1: {"font": TEXT_DARK, "fill": pygame.Color(239, 229, 218)},
    2: {"font": TEXT_DARK, "fill": pygame.Color(238, 225, 199)},
    3: {"font": TEXT_LIGHT, "fill": pygame.Color(242, 177, 121)},
    4: {"font": TEXT_LIGHT, "fill": pygame.Color(245, 149, 99)}
}

# Define constants for the screen width and height
BORDER_WIDTH = 10
TILE_SIZE = 100
NUMBER_OF_ROWS = NUMBER_OF_COLUMNS = 4
SCREEN_WIDTH = SCREEN_HEIGHT = ((NUMBER_OF_ROWS + 1) * BORDER_WIDTH) + (NUMBER_OF_ROWS * TILE_SIZE)

FONT_SIZE = 24



class Tile(pygame.sprite.Sprite):

    def __init__(self, row, column, value=0):
        super(Tile, self).__init__()
        self.font = pygame.font.Font(pygame.font.get_default_font(), FONT_SIZE)
        self.x_pos = BORDER_WIDTH + (row * (BORDER_WIDTH + TILE_SIZE))
        self.y_pos = BORDER_WIDTH + (column * (BORDER_WIDTH + TILE_SIZE))
        self.surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.value = -1
        self.update(value)
    
    def update(self, value):
        self.change_fill(value)
        self.change_text(value)
        self.value = value

    def change_text(self, value):
        text_colour = CELL_STYLES[value]["font"]
        text_surface = self.font.render(str(value), True, text_colour, None)
        text_rectangle = text_surface.get_rect(center=(TILE_SIZE/2, TILE_SIZE/2))
        self.surface.blit(text_surface, text_rectangle)

    def change_fill(self, value):
        fill_colour = CELL_STYLES[value]["fill"]
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
        tiles = []
        for row in range(0, NUMBER_OF_ROWS):
            row_of_tiles = []
            for column in range(0, NUMBER_OF_COLUMNS):
                tile = Tile(row, column)
                row_of_tiles.append(tile)
                self.all_tiles.add(tile)
            tiles.append(row_of_tiles)
        return tiles

    def update_tiles(self, tile_values):
        for row in range(0, NUMBER_OF_ROWS):
            for column in range(0, NUMBER_OF_COLUMNS):
                self.tiles[row][column].update(tile_values[row][column])

    def draw_tiles(self):
        for tile in self.all_tiles:
            self.screen.blit(tile.surface, (tile.x_pos, tile.y_pos))

    @staticmethod
    def generate_random_tile_values():
        return [
            [
                random.randint(0, 4) for column in range(0, NUMBER_OF_COLUMNS)
            ] 
            for row in range(0, NUMBER_OF_ROWS)
        ]
        # tile_values = []
        # for row in range(0, NUMBER_OF_ROWS):
        #     row_of_tiles = []
        #     for column in range(0, NUMBER_OF_COLUMNS):
        #         row_of_tiles.append(random.randint(0, 4))
        #     tile_values.append(row_of_tiles)
        # return tile_values

# Initialize pygame
pygame.init()
game = Game()

# Variable to keep the main loop running
running = True

# Main loop
while running:
    # Look at every event in the queue
    for event in pygame.event.get():
        # Did the user hit a key?
        if event.type == KEYDOWN:
            # Was it the Escape key? If so, stop the loop.
            if event.key == K_ESCAPE:
                running = False
            else:
                tile_values = Game.generate_random_tile_values()
                game.update_tiles(tile_values)
                game.draw_tiles()

        # Did the user click the window close button? If so, stop the loop.
        elif event.type == QUIT:
            running = False

    pygame.display.flip()


