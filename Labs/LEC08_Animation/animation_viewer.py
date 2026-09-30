from pico2d import *
from pathlib import Path


ANIMATION_FPS = 8


def play_animation(image, frames, elapsed, x, y, scale):
    frame_index = int(elapsed * ANIMATION_FPS) % len(frames)
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
    sonic_image = load_image(str(Path(__file__).with_name("sonic-sprite.png")))
    sonic_x = 400
    sonic_y = 300
    sonic_scale = 4
    run_frames = (
        (1, 447, 29, 39, 18),
        (31, 447, 26, 38, 14.5),
        (58, 447, 28, 39, 17),
        (86, 447, 30, 38, 17.5),
        (118, 447, 30, 38, 17.5),
        (150, 447, 30, 38, 13.5),
        (182, 447, 29, 38, 11.5),
        (211, 448, 28, 38, 17.5),
    )
    roll_frames = tuple((left, 292, 30, 27, 15) for left in (1, 36, 70, 105, 139, 174))
    run_duration = len(run_frames) / ANIMATION_FPS
    cycle_duration = (len(run_frames) + len(roll_frames)) / ANIMATION_FPS
    animation_start = get_time()

    running = True
    while running:
        for event in get_events():
            if event.type == SDL_QUIT:
                running = False
        clear_canvas()
        cycle_elapsed = (get_time() - animation_start) % cycle_duration
        if cycle_elapsed < run_duration:
            play_animation(sonic_image, run_frames, cycle_elapsed, sonic_x, sonic_y, sonic_scale)
        else:
            play_animation(
                sonic_image, roll_frames, cycle_elapsed - run_duration,
                sonic_x, sonic_y, sonic_scale
            )
        update_canvas()
        delay(0.016)

    close_canvas()


if __name__ == '__main__':
    run()
