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
