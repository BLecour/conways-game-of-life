import warp as wp
import numpy as np
import pygame
import sys

pygame.init()
WIDTH, HEIGHT = 1280, 1000
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Conway's Game of Life")
clock = pygame.time.Clock()

GRID_SIZE = 50
GRID_COLOR = (100, 100, 100)
SELECTED_COLOR = (0, 0, 0)
BG_COLOR = (255, 255, 255)
LEFT_DRAG_THRESHOLD = 6
ZOOM_MIN = 0.2
ZOOM_MAX = 5.0
ZOOM_SPEED = 0.1
BUTTON_RECT = pygame.Rect(20, 20, 120, 40)
BUTTON_COLOR = (70, 70, 70)
BUTTON_HOVER = (100, 100, 100)
BUTTON_TEXT_COLOR = (240, 240, 240)

font = pygame.font.SysFont(None, 28)
zoom = 1.0
camera_offset = pygame.Vector2(0, 0)
left_down = False
left_dragging = False
click_started_on_button = False
left_start = pygame.Vector2()
last_mouse = pygame.Vector2()
middle_dragging = False
running_simulation = False
selected_cell = None
cells = []

@wp.kernel
def cells_update(input: wp.array(dtype=wp.bool, ndim=2), output: wp.array(dtype=wp.bool, ndim=2), x_len: int, y_len: int):

    x, y = wp.tid()

    cell_neighbours = wp.int32(0)
    top = wp.int32(input[x, y-1])
    top_right = wp.int32(input[x+1, y-1])
    right = wp.int32(input[x+1, y])
    bottom_right = wp.int32(input[x+1, y+1])
    bottom = wp.int32(input[x, y+1])
    bottom_left = wp.int32(input[x-1, y+1])
    left = wp.int32(input[x-1, y])
    top_left = wp.int32(input[x-1, y-1])

    # Handle border cases
    if x == 0:
        if y == 0: # Top left
            cell_neighbours += right + bottom_right + bottom
        elif y == y_len: # Bottom left
            cell_neighbours += top + top_right + right
        else: # Left
            cell_neighbours += top + top_right + right + bottom_right + bottom
    elif x == x_len:
        if y == 0: # Top right
            cell_neighbours += bottom + bottom_left + left
        elif y == y_len: # Bottom right
            cell_neighbours += top + left + top_left
        else: # Right
            cell_neighbours += top + bottom + bottom_left + left + top_left
    elif y == 0: # Top
        cell_neighbours += right + bottom_right + bottom + bottom_left + left
    elif y == y_len: # Bottom
        cell_neighbours += top + top_right + right + left + top_left
    else: # Not an edge
        cell_neighbours += top + top_right + right + bottom_right + bottom + bottom_left + left + top_left

    # Cell rules
    if input[x, y]:
        # Live cell with less than two neighbours dies
        if cell_neighbours < 2:
            output[x, y] = False

        # Live cell with two or three neighbours lives on
        elif cell_neighbours == 2 or cell_neighbours == 3:
            output[x, y] = True

        # Live cell with more than three neighbours dies
        else:
            output[x, y] = False
        return
    
    # Dead cell with three neighbours becomes live
    if not input[x, y] and cell_neighbours == 3:
        output[x, y] = True
        return
    
    # Set cell to dead if no cases above match
    output[x, y] = False


def world_to_screen(world):
    return (pygame.Vector2(world) - camera_offset) * zoom

def screen_to_world(screen_pos):
    return pygame.Vector2(screen_pos) / zoom + camera_offset

def draw_grid():
    start = screen_to_world((0, 0))
    end = screen_to_world((WIDTH, HEIGHT))

    start_x = int(start.x // GRID_SIZE) - 1
    end_x = int(end.x // GRID_SIZE) + 1
    start_y = int(start.y // GRID_SIZE) - 1
    end_y = int(end.y // GRID_SIZE) + 1

    for cell in cells:
        x, y = cell

        top_left = world_to_screen((x * GRID_SIZE, y * GRID_SIZE))
        size = GRID_SIZE * zoom

        rect = pygame.Rect(
            round(top_left.x),
            round(top_left.y),
            round(size),
            round(size),
        )

        pygame.draw.rect(screen, SELECTED_COLOR, rect)

    for x in range(start_x, end_x + 1):
        sx = world_to_screen((x * GRID_SIZE, 0)).x
        pygame.draw.line(screen, GRID_COLOR, (sx, 0), (sx, HEIGHT), 1)

    for y in range(start_y, end_y + 1):
        sy = world_to_screen((0, y * GRID_SIZE)).y
        pygame.draw.line(screen, GRID_COLOR, (0, sy), (WIDTH, sy), 1)


def draw_play_pause_button():
    mouse_pos = pygame.mouse.get_pos()
    hovered = BUTTON_RECT.collidepoint(mouse_pos)

    color = BUTTON_HOVER if hovered else BUTTON_COLOR
    pygame.draw.rect(screen, color, BUTTON_RECT, border_radius=6)

    label = "Pause" if running_simulation else "Play"
    text_surf = font.render(label, True, BUTTON_TEXT_COLOR)
    text_rect = text_surf.get_rect(center=BUTTON_RECT.center)

    screen.blit(text_surf, text_rect)

wp.init()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Scrolling
        if event.type == pygame.MOUSEWHEEL:
            mouse_screen = pygame.mouse.get_pos()
            mouse_world = screen_to_world(mouse_screen)
            zoom *= 1 + event.y * ZOOM_SPEED
            zoom = max(ZOOM_MIN, min(zoom, ZOOM_MAX))
            camera_offset = mouse_world - pygame.Vector2(mouse_screen) / zoom

        # Left mouse drag
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if BUTTON_RECT.collidepoint(event.pos):
                    click_started_on_button = True
                    running_simulation = not running_simulation
                    continue  # prevent grid click underneath
                else:
                    click_started_on_button = False
                    left_down = True
                    left_dragging = False
                    left_start = pygame.Vector2(event.pos)
                    last_mouse = pygame.Vector2(event.pos)
            if event.button == 2:
                middle_dragging = True
                last_mouse = pygame.Vector2(event.pos)

        # Left mouse click
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if not click_started_on_button and not left_dragging:
                    world = screen_to_world(event.pos)
                    cell = (int(world.x // GRID_SIZE), int(world.y // GRID_SIZE))
                    if cell in cells:
                        cells.remove(cell)
                    else:
                        cells.append(cell)
                left_down = False
                left_dragging = False
                click_started_on_button = False

            if event.button == 2:
                middle_dragging = False

        # Dragging
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.Vector2(event.pos)
            if left_down:
                if not left_dragging:
                    if (mouse_pos - left_start).length() > LEFT_DRAG_THRESHOLD:
                        left_dragging = True
                if left_dragging:
                    delta = mouse_pos - last_mouse
                    camera_offset -= delta / zoom
                    last_mouse = mouse_pos
            if middle_dragging:
                delta = mouse_pos - last_mouse
                camera_offset -= delta / zoom
                last_mouse = mouse_pos

    if running_simulation:
        if cells:
            x, y = zip(*cells)
            min_x = min(x)
            min_y = min(y)
            max_x = max(x)
            max_y = max(y)
            x_len = max_x - min_x + 3
            y_len = max_y - min_y + 3
            print(x_len, y_len)
            cell_bools = [[False]*y_len for i in range(x_len)]
            cell_bools = np.full(shape=(x_len, y_len), fill_value=False, dtype=wp.bool)
            for cell in cells:
                cell_bools[cell[0]-min_x+1][cell[1]-min_y+1] = True
            input_array = wp.array(cell_bools, shape=(x_len, y_len), dtype=wp.bool)
            output_array = wp.full(value=False, shape=(x_len, y_len), dtype=wp.bool)
            wp.launch(
                kernel=cells_update,
                dim=(x_len, y_len),
                inputs=[input_array, output_array, x_len-1, y_len-1],
                device="cuda"
            )
            wp.synchronize()
            output = output_array.numpy()
            cells.clear()
            for i in range(x_len):
                for j in range(y_len):
                    if output[i][j]:
                        cells.append((i+min_x-1, j+min_y-1))
            

    screen.fill(BG_COLOR)
    draw_grid()
    draw_play_pause_button()
    pygame.display.flip()
    clock.tick(2)