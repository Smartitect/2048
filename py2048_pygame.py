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

# Initialize pygame
pygame.init()

# Define constants for the screen width and height
BORDER_WIDTH = 10
TILE_SIZE = 100
NUMBER_OF_ROWS = NUMBER_OF_COLUMNS = 4
SCREEN_WIDTH = SCREEN_HEIGHT = ((NUMBER_OF_ROWS + 1) * BORDER_WIDTH) + (NUMBER_OF_ROWS * TILE_SIZE)

FONT_SIZE = 24
FONT = pygame.font.Font(pygame.font.get_default_font(), FONT_SIZE)

# Create the screen object
# The size is determined by the constant SCREEN_WIDTH and SCREEN_HEIGHT
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
screen.fill(BACKGROUND)

# Variable to keep the main loop running
running = True


class Tile(pygame.sprite.Sprite):

    def __init__(self, row, column, value=0):
        super(Tile, self).__init__()
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
        text_surface = FONT.render(str(value), True, text_colour, None)
        text_rectangle = text_surface.get_rect(center=(TILE_SIZE/2, TILE_SIZE/2))
        self.surface.blit(text_surface, text_rectangle)

    def change_fill(self, value):
        fill_colour = CELL_STYLES[value]["fill"]
        self.surface.fill(fill_colour)

all_tiles = pygame.sprite.Group()

def initialise_tiles():

    tiles = []

    for row in range(0, NUMBER_OF_ROWS):
        row_of_tiles = []
        for column in range(0, NUMBER_OF_COLUMNS):
            tile = Tile(row, column, random.randint(0, 4))
            row_of_tiles.append(tile)
            all_tiles.add(tile)
        tiles.append(row_of_tiles)
    return tiles

def draw_tiles(screen):
    for tile in all_tiles:
        screen.blit(tile.surface, (tile.x_pos, tile.y_pos))

def draw_tiles_old(screen, tiles):
    for row in range(0, NUMBER_OF_ROWS):
        for column in range(0, NUMBER_OF_COLUMNS):
            tile = tiles[row][column]
            screen.blit(tile.surface, (tile.x_pos, tile.y_pos))

tiles = initialise_tiles()
draw_tiles(screen)

pygame.display.flip()

# Main loop
while running:
    # Look at every event in the queue
    for event in pygame.event.get():
        # Did the user hit a key?
        if event.type == KEYDOWN:
            # Was it the Escape key? If so, stop the loop.
            if event.key == K_ESCAPE:
                running = False


        # Did the user click the window close button? If so, stop the loop.
        elif event.type == QUIT:
            running = False