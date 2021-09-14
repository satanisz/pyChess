import pygame

# --- constants --- (UPPER_CASE names)

SCREEN_WIDTH = 430
SCREEN_HEIGHT = 410
WHITE  = (255, 255, 255)
RED    = (255,   0,   0)
GREEN  = (  0, 255,   0)
BLUE   = (  0,   0, 255)


# --- main ---

# - init -

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# - objects -
rectangle2 = pygame.rect.Rect(266, 224, 30, 30)
rectangle1 = pygame.rect.Rect(176, 134, 30, 30)
rectangle1_draging = False

# - mainloop -

clock = pygame.time.Clock()

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
                rectangle1.x -= rectangle1.x % 30
                rectangle1.y -= rectangle1.y % 30

        elif event.type == pygame.MOUSEMOTION:
            if rectangle1_draging:
                mouse_x, mouse_y = event.pos
                rectangle1.x = mouse_x + offset_x
                rectangle1.y = mouse_y + offset_y




    # - draws (without updates) -

    screen.fill(WHITE)
    pygame.draw.rect(screen, RED, rectangle1)
    pygame.draw.rect(screen, BLUE, rectangle2)
    pygame.display.flip()

    # - constant game speed / FPS -

    clock.tick(FPS)

# - end -

pygame.quit()