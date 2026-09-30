from pico2d import *
from pathlib import Path


def run():
    open_canvas(800, 600)
    sonic_image = load_image(str(Path(__file__).with_name("sonic-sprite.png")))
    sonic_x = 400
    sonic_y = 300

    running = True
    while running:
        for event in get_events():
            if event.type == SDL_QUIT:
                running = False
        clear_canvas()
        sonic_image.clip_draw(0, 447, 31, 39, sonic_x, sonic_y)
        update_canvas()
        delay(0.016)

    close_canvas()


if __name__ == '__main__':
    run()
