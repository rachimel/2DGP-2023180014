import json
from pathlib import Path

import pico2d
from pico2d import *

def play_animation(image, frames, elapsed, x, y, scale, fps):
    frame_index = int(elapsed * fps) % len(frames)
    frame_left, frame_bottom, frame_width, frame_height, foot_x = frames[frame_index]
    draw_width = frame_width * scale
    draw_height = frame_height * scale
    draw_x = x + draw_width // 2 - foot_x * scale
    draw_y = y + draw_height // 2
    image.clip_draw(
        frame_left, frame_bottom, frame_width, frame_height,
        draw_x, draw_y, draw_width, draw_height
    )


def run():
    open_canvas(800, 600)
    with Path(__file__).with_name("sonic_animations.json").open(encoding="utf-8") as animation_file:
        animation_data = json.load(animation_file)
    animation_fps = animation_data["fps"]
    animation_rows = animation_data["animations"]
    repeat_count = 5
    pause_duration = 1.0
    sonic_image = load_image(str(Path(__file__).with_name("sonic-sprite.png")))
    font_path = Path(pico2d.__file__).parent / "data" / "ConsolaMalgun.ttf"
    font = load_font(str(font_path), 24)
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
        current_frame = playback_frame % len(frames) + 1
        font.draw(10, 570, f"프레임 : {current_frame} / {len(frames)}", (255, 255, 255))
        font.draw(
            10, 540, f"애니메이션 : {animation_index + 1} / {len(animation_rows)}",
            (255, 255, 255)
        )
        update_canvas()
        delay(0.016)

    close_canvas()


if __name__ == '__main__':
    run()
