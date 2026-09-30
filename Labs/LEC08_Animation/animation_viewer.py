from pico2d import *
from pathlib import Path


def run():
    open_canvas(800, 600)
    sonic_image = load_image(str(Path(__file__).with_name("sonic-sprite.png")))
    sonic_x = 400
    sonic_y = 300
    sonic_scale = 4
    frame_rects = (
        (1, 447, 29, 39),
        (31, 447, 26, 38),
        (58, 447, 28, 39),
        (86, 447, 30, 38),
        (118, 447, 30, 38),
        (150, 447, 30, 38),
        (182, 447, 29, 38),
        (211, 448, 28, 38),
    )
    animation_start = get_time()

    running = True
    while running:
        for event in get_events():
            if event.type == SDL_QUIT:
                running = False
        clear_canvas()
        frame_index = int((get_time() - animation_start) * 8) % len(frame_rects)
        frame_left, frame_bottom, frame_width, frame_height = frame_rects[frame_index]
        draw_width = frame_width * sonic_scale
        draw_height = frame_height * sonic_scale
        draw_y = sonic_y + draw_height // 2
        sonic_image.clip_draw(
            frame_left, frame_bottom, frame_width, frame_height,
            sonic_x, draw_y, draw_width, draw_height
        )
        update_canvas()
        delay(0.016)

    close_canvas()


if __name__ == '__main__':
    run()
