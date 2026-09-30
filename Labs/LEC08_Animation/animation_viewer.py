import json
from pathlib import Path

from pico2d import *

from sonic_animations import play_animation


def run():
    open_canvas(800, 600)
    with Path(__file__).with_name("sonic_animations.json").open(encoding="utf-8") as animation_file:
        animation_data = json.load(animation_file)
    animation_fps = animation_data["fps"]
    animation_rows = animation_data["animations"]
    repeat_count = 5
    pause_duration = 1.0
    sonic_image = load_image(str(Path(__file__).with_name("sonic-sprite.png")))
    sonic_x = 400
    sonic_y = 300
    sonic_scale = 4
    animation_index = 0
    animation_start = get_time()

    running = True
    while running:
        for event in get_events():
            if event.type == SDL_QUIT:
                running = False
        clear_canvas()
        current_time = get_time()
        elapsed = current_time - animation_start
        frames = animation_rows[animation_index]
        animation_duration = len(frames) * repeat_count / animation_fps
        while elapsed >= animation_duration + pause_duration:
            animation_start += animation_duration + pause_duration
            animation_index = (animation_index + 1) % len(animation_rows)
            elapsed = current_time - animation_start
            frames = animation_rows[animation_index]
            animation_duration = len(frames) * repeat_count / animation_fps
        playback_frame = min(int(elapsed * animation_fps), len(frames) * repeat_count - 1)
        play_animation(
            sonic_image, frames, playback_frame / animation_fps,
            sonic_x, sonic_y, sonic_scale, animation_fps
        )
        update_canvas()
        delay(0.016)

    close_canvas()


if __name__ == '__main__':
    run()
