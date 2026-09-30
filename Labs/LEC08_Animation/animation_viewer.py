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


def centered_frames(rects):
    return tuple(
        (left, bottom, width, height, width / 2)
        for left, bottom, width, height in rects
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
        (211, 448, 29, 38, 18),
        (240, 448, 29, 38, 18),
        (270, 448, 24, 32, 12),
        (302, 448, 29, 26, 13),
    )
    animation_rows = (
        run_frames,
        centered_frames((
            (8, 408, 26, 37), (37, 408, 27, 37), (65, 407, 31, 38),
            (97, 408, 37, 37), (135, 410, 32, 35), (170, 408, 32, 38),
            (206, 408, 26, 38), (238, 408, 24, 37), (263, 408, 30, 37),
            (295, 408, 36, 37), (334, 409, 32, 36), (370, 408, 29, 38),
        )),
        centered_frames((
            (1, 361, 33, 40), (39, 362, 35, 39), (89, 362, 35, 38),
            (130, 362, 34, 40), (181, 362, 34, 40), (228, 363, 33, 39),
        )),
        centered_frames((
            (1, 326, 29, 30), (35, 327, 29, 31), (67, 327, 30, 29),
            (98, 327, 31, 29), (131, 327, 29, 30), (162, 326, 29, 31),
            (193, 326, 30, 29), (230, 326, 31, 29), (268, 325, 30, 30),
        )),
        centered_frames((
            (1, 292, 30, 27), (36, 292, 29, 27), (70, 292, 29, 27),
            (105, 292, 29, 27), (139, 292, 29, 27), (174, 292, 29, 27),
        )),
        centered_frames((
            (1, 251, 29, 35), (36, 251, 30, 35), (74, 251, 31, 35),
            (111, 251, 31, 36), (149, 251, 30, 35), (186, 251, 31, 36),
        )),
        centered_frames((
            (1, 207, 29, 35), (36, 207, 30, 35), (72, 208, 39, 31),
            (123, 208, 39, 32), (172, 208, 39, 31), (218, 208, 38, 32),
        )),
        centered_frames((
            (1, 154, 24, 45), (31, 154, 29, 44), (65, 154, 20, 44),
            (90, 155, 25, 43), (119, 155, 25, 43), (149, 154, 20, 44),
            (184, 156, 40, 28), (232, 157, 39, 27),
        )),
        centered_frames((
            (1, 108, 27, 38), (31, 110, 31, 36), (64, 110, 31, 36),
            (99, 110, 33, 38), (136, 110, 32, 36), (176, 110, 33, 36),
            (217, 110, 33, 36), (254, 111, 33, 36),
        )),
        centered_frames((
            (6, 56, 34, 40), (49, 56, 34, 43),
            (96, 59, 23, 39), (125, 59, 23, 39),
        )),
    )
    total_frames = sum(len(frames) for frames in animation_rows)
    animation_start = get_time()

    running = True
    while running:
        for event in get_events():
            if event.type == SDL_QUIT:
                running = False
        clear_canvas()
        frame_index = int((get_time() - animation_start) * ANIMATION_FPS) % total_frames
        for frames in animation_rows:
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
