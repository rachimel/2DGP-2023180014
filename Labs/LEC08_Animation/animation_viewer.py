from pico2d import *


def run():
    open_canvas(800, 600)

    running = True
    while running:
        for event in get_events():
            if event.type == SDL_QUIT:
                running = False
        clear_canvas()
        update_canvas()
        delay(0.016)

    close_canvas()


if __name__ == '__main__':
    run()
