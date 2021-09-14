import itertools
import pygame


# - init -

pygame.init()

BLACK = pygame.Color('black')
WHITE = pygame.Color('white') #(255, 255, 255)
RED    = (255,   0,   0)
GREEN  = (  0, 255,   0)
BLUE   = (  0,   0, 255)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 50
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

shift_x = 100
shift_y = 100
# - objects -
piece_size = 45
tile_size = 55

rectangle2 = pygame.rect.Rect(  tile_size + shift_x+5, 2*tile_size + shift_y+5, piece_size, piece_size)
rectangle1 = pygame.rect.Rect(5*tile_size + shift_x+5, 5*tile_size + shift_y+5, piece_size, piece_size)
rectangle1_draging = False

clock = pygame.time.Clock()

colors = itertools.cycle((WHITE, BLACK))

width, height = 8*tile_size, 8*tile_size
background = pygame.Surface((width, height))
for y in range(0, height, tile_size):
    for x in range(0, width, tile_size):
        rect = (x, y, tile_size, tile_size)
        pygame.draw.rect(background, next(colors), rect)
    next(colors)

# ---
piece_stand = pygame.Surface((width, height))

rect = (0, 0, tile_size, tile_size)
pygame.draw.rect(piece_stand, next(colors), rect)

# ---


running = True
while running:

    # - events -

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if rectangle1.collidepoint(event.pos):
                    rectangle1_draging = True
                    mouse_x, mouse_y = event.pos
                    offset_x = rectangle1.x - mouse_x
                    offset_y = rectangle1.y - mouse_y


        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                rectangle1_draging = False
                rectangle1.x -= rectangle1.x % tile_size + 5
                rectangle1.y -= rectangle1.y % tile_size + 5

        elif event.type == pygame.MOUSEMOTION:
            if rectangle1_draging:
                mouse_x, mouse_y = event.pos
                rectangle1.x = mouse_x + offset_x
                rectangle1.y = mouse_y + offset_y


    # - draws (without updates) -

    screen.fill((60, 70, 90)) # WHITE
    screen.blit(background, (shift_x, shift_y))

    pygame.draw.rect(screen, RED, rectangle1)
    pygame.draw.rect(screen, BLUE, rectangle2)
    pygame.display.flip()



    # - constant game speed / FPS -

    clock.tick(FPS)



pygame.quit()