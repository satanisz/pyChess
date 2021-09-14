"""Chess game, for learning to grab images from a sprite sheet."""

import sys
import itertools
import pygame

from settings import SET
from chess_set import ChessSet


class ChessGame:
    """Overall class to manage game assets and behavior."""

    def __init__(self):
        """Initialize the game, and create resources."""
        pygame.init()
        self.wqueen_draging = False
        # self.screen = pygame.display.set_mode(
        #         (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        # pygame.display.set_caption("Chess")
        #
        self.chess_set = ChessSet(self)
        self.screen = pygame.display.set_mode((SET.SCREEN_WIDTH, SET.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        colors = itertools.cycle((SET.WHITE, SET.BLACK))

        width, height = 8 * SET.tile_size, 8 * SET.tile_size
        self.background = pygame.Surface((width, height))
        for y in range(0, height, SET.tile_size):
            for x in range(0, width, SET.tile_size):
                rect = (x, y, SET.tile_size, SET.tile_size)
                pygame.draw.rect(self.background, next(colors), rect)
            next(colors)

        self.wqueen = self.chess_set.pieces[1]
        self.wqueen.x = 5*SET.tile_size + SET.shift_x+5
        self.wqueen.y = 5*SET.tile_size + SET.shift_y+5

    def run_game(self):
        """Start the main loop for the game."""
        while True:
            self._check_events()
            self._update_screen()


    def _check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.wqueen.collidepoint(event.pos):
                        self.wqueen_draging = True
                        mouse_x, mouse_y = event.pos
                        offset_x = self.wqueen.x - mouse_x
                        offset_y = self.wqueen.y - mouse_y

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.wqueen_draging = False
                    self.wqueen.x -= ((self.wqueen.x + 28 + 7) % SET.tile_size) - 28
                    self.wqueen.y -= ((self.wqueen.y + 28 + 7) % SET.tile_size) - 28

            elif event.type == pygame.MOUSEMOTION:
                if self.wqueen_draging:
                    mouse_x, mouse_y = event.pos
                    self.wqueen.x = mouse_x + offset_x
                    self.wqueen.y = mouse_y + offset_y

    def _update_screen(self):
        self.screen.fill(SET.BG_COLOR)
        self.screen.blit(self.background, (SET.shift_x, SET.shift_y))
        # Draw a row of black pieces.
        # for index, piece in enumerate(self.chess_set.pieces[6:]):
        #     piece.x = index * 320
        #     piece.blitme()

        # Draw a row of white pieces.
        # for index, piece in enumerate(self.chess_set.pieces[:6]):
        #     piece.x = index * 320
        #     piece.y = 320
        #     piece.blitme()



        self.wqueen.blitme()

        # print(wqueen.name, wqueen.color)

        pygame.display.flip()


        # - constant game speed / FPS -

        self.clock.tick(SET.FPS)





if __name__ == '__main__':
    chess_game = ChessGame()
    #chess_game.run_game()