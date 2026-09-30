from pathlib import Path

from pico2d import *

from sonic_animations import ANIMATION_FPS, ANIMATION_ROWS, TOTAL_FRAMES, play_animation


def run():
    open_canvas(800, 600)
    sonic_image = load_image(str(Path(__file__).with_name("sonic-sprite.png")))
    sonic_x = 400
    sonic_y = 300
    sonic_scale = 4
    animation_start = get_time()

    running = True
    while running:
        for event in get_events():
            if event.type == SDL_QUIT:
                running = False
        clear_canvas()
        frame_index = int((get_time() - animation_start) * ANIMATION_FPS) % TOTAL_FRAMES
        for frames in ANIMATION_ROWS:
            if frame_index < len(frames):
                play_animation(
                    sonic_image, frames, frame_index / ANIMATION_FPS,
                    sonic_x, sonic_y, sonic_scale
                )
                break
            frame_index -= len(frames)
        update_canvas()
        delay(0.016)

    close_canvas()


if __name__ == '__main__':
    run()
