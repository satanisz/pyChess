"""Display the piece images bundled with PyChess."""

import pygame

from pychess.assets import sprite_sheet_path

pygame.init()
screen = pygame.display.set_mode((800, 800))
pygame.display.set_caption("Image")

with sprite_sheet_path() as path:
    image = pygame.image.load(path).convert_alpha()

screen.fill("white")
screen.blit(image, (0, 0))
pygame.display.flip()

while pygame.event.wait().type != pygame.QUIT:
    pass

pygame.quit()
