from pico2d import *
import math
import os

W, H = 800, 600
CX, CY = W // 2, H // 2
R = 120
SIZE = 220
SPEED = 0.25  # 한 운동을 4초 정도에 1회 완료

image = None
mode = 0          # 0: 원, 1: 사각형, 2: 삼각형
progress = 0.0    # 0.0 ~ 1.0
x, y = CX, CY


def lerp(a, b, t):
    return a + (b - a) * t


def point_on_polygon(vertices, t):
    count = len(vertices)
    p = t * count
    i = int(p) % count
    local_t = p - int(p)

    x1, y1 = vertices[i]
    x2, y2 = vertices[(i + 1) % count]

    return lerp(x1, x2, local_t), lerp(y1, y2, local_t)


def update(dt):
    global mode, progress, x, y

    progress += SPEED * dt

    if progress >= 1.0:
        progress -= 1.0
        mode = (mode + 1) % 3

    if mode == 0:
        angle = progress * 2.0 * math.pi
        x = CX + math.cos(angle) * R
        y = CY + math.sin(angle) * R

    elif mode == 1:
        s = SIZE / 2
        square = [
            (CX - s, CY - s),
            (CX + s, CY - s),
            (CX + s, CY + s),
            (CX - s, CY + s)
        ]
        x, y = point_on_polygon(square, progress)

    else:
        h = SIZE * math.sqrt(3) / 2
        triangle = [
            (CX - SIZE / 2, CY - h / 3),
            (CX + SIZE / 2, CY - h / 3),
            (CX, CY + 2 * h / 3)
        ]
        x, y = point_on_polygon(triangle, progress)


def handle_events():
    for event in get_events():
        if event.type == SDL_QUIT:
            return False
        if event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            return False
    return True


def main():
    global image

    open_canvas(W, H)
    image = load_image(os.path.join(os.path.dirname(__file__), 'character.png'))

    running = True
    previous = get_time()

    while running:
        now = get_time()
        dt = now - previous
        previous = now

        running = handle_events()
        update(dt)

        clear_canvas()
        image.draw(x, y)
        update_canvas()

        delay(0.01)

    close_canvas()


if __name__ == '__main__':
    main()
