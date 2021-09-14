import pygame
from pygame.locals import *
import chess
import cairosvg
import chess.svg
import chess.pgn

##Setup Pygame:
pygame.init()

width, height = 640, 640
screen = pygame.display.set_mode((width, height))

## MAIN ##

board = chess.Board()

# Step 1: Create image
boardsvg = chess.svg.board(board=board)
f = open("image.SVG", "w")
f.write(boardsvg)
f.close()

# scale
cairosvg.svg2png(url="image.svg", write_to="image_scaled.png", scale=3.0)

# Step2: Blit the image
image = pygame.image.load('image_scaled.png')
image = pygame.transform.scale(image, (640, 640))
screen.blit(image, (0, 0))
pygame.display.flip()