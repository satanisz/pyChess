from pathlib import Path

import cairosvg
import chess
import chess.svg
import pygame

##Setup Pygame:
pygame.init()

width, height = 640, 640
screen = pygame.display.set_mode((width, height))

## MAIN ##

board = chess.Board()

# Step 1: Create image
boardsvg = chess.svg.board(board=board)
svg_path = Path("image.svg")
svg_path.write_text(boardsvg)

# scale
png_path = Path("image_scaled.png")
cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), scale=3.0)

# Step2: Blit the image
image = pygame.image.load(str(png_path))
image = pygame.transform.scale(image, (640, 640))
screen.blit(image, (0, 0))
pygame.display.flip()
