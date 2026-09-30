from pico2d import *
from pathlib import Path


def run():
    open_canvas(800, 600)
    sonic_image = load_image(str(Path(__file__).with_name("sonic-sprite.png")))
    sonic_x = 400
    sonic_y = 300
    frame_bounds = (0, 30, 57, 86, 116, 148, 180, 209, 239)
    animation_start = get_time()

    running = True
    while running:
        for event in get_events():
            if event.type == SDL_QUIT:
                running = False
        clear_canvas()
        frame_index = int((get_time() - animation_start) * 8) % (len(frame_bounds) - 1)
        frame_left = frame_bounds[frame_index]
        frame_width = frame_bounds[frame_index + 1] - frame_left
        sonic_image.clip_draw(frame_left, 447, frame_width, 39, sonic_x, sonic_y, 120, 150)
        update_canvas()
        delay(0.016)

    close_canvas()


if __name__ == '__main__':
    run()
