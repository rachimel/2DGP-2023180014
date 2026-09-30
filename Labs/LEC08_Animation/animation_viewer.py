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
    pause_frames = animation_fps
    total_frames = sum(len(frames) * repeat_count + pause_frames for frames in animation_rows)
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
        frame_index = int((get_time() - animation_start) * animation_fps) % total_frames
        for frames in animation_rows:
            animation_frames = len(frames) * repeat_count
            if frame_index < animation_frames + pause_frames:
                playback_frame = min(frame_index, animation_frames - 1) % len(frames)
                play_animation(
                    sonic_image, frames, playback_frame / animation_fps,
                    sonic_x, sonic_y, sonic_scale, animation_fps
                )
                break
            frame_index -= animation_frames + pause_frames
        update_canvas()
        delay(0.016)

    close_canvas()


if __name__ == '__main__':
    run()
