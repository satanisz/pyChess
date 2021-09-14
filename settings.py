
import pygame


#
class SET(object):
    # static CLASS
    FPS = 50
    BG_COLOR = (110, 0, 110) # (225, 225, 225)
    BLACK = pygame.Color('black')
    WHITE = pygame.Color('white')  # (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    SCALE = 3

    shift_x = 100
    shift_y = 100
    # - objects -
    piece_size = 46
    tile_size = 56

    # piece_width, piece_height = int(SCREEN_WIDTH/SCALE), int(SCREEN_HEIGHT/SCALE)

    piece_width = piece_height = piece_size


