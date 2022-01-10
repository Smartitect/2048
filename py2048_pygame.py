# Import the pygame module
import pygame

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

# Variable to keep the main loop running
running = True

def initialise_tiles():

    tiles = []

    for row in range(0, NUMBER_OF_ROWS):

        row_of_tiles = []

        for column in range(0, NUMBER_OF_COLUMNS):
    
            tile_surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
            tile_surface.fill((100, 100, 100))

            initial_string = '{}_{}'.format(row, column)
            tile_text = FONT.render(initial_string, True, (255, 255, 255), None)
            text_rectangle = tile_text.get_rect(center=(TILE_SIZE/2, TILE_SIZE/2))
            tile_surface.blit(tile_text, text_rectangle)

            row_of_tiles.append(tile_surface)
        
        tiles.append(row_of_tiles)

    return tiles

def draw_tiles(screen, tiles):
    for row in range(0, NUMBER_OF_ROWS):
        x_pos = BORDER_WIDTH + (row * (BORDER_WIDTH + TILE_SIZE))
        for column in range(0, NUMBER_OF_COLUMNS):
            y_pos = BORDER_WIDTH + (column * (BORDER_WIDTH + TILE_SIZE))
            screen.blit(tiles[row][column], (x_pos, y_pos))

tiles = initialise_tiles()
draw_tiles(screen, tiles)

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