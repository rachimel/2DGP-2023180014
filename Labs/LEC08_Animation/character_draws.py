from pico2d import *
from pathlib import Path

def run():
    open_canvas()
    grass = load_image(str(Path(__file__).with_name("grass.png")))
    character = load_image(str(Path(__file__).with_name("animation_sheet.png")))
    running = True

    frame = 0
    yframe = 0
    for x in range(0, 800, 5):
        clear_canvas()
        grass.draw(400, 30)
        character.clip_composite_draw(
            frame * 100, 300,
            100, 100,
            0, '',
            100, 90,
            100,100
        )
        character.clip_composite_draw(
            frame * 100, 200,
            100, 100,
            0, '',
            200, 90,
            100,100
        )
        character.clip_composite_draw(
            frame * 100, 100,
            100, 100,
            0, '',
            300, 90,
            100,100
        )
        character.clip_composite_draw(
            frame * 100, 0,
            100, 100,
            0, '',
            400, 90,
            100,100
        )

        character.clip_composite_draw(
            frame * 100, (3 - yframe) * 100,
            100, 100,
            0, '',
            x, 90,
            100,100
        )
        update_canvas()

        frame = (frame + 1)
        if(frame >= 8):
            frame = 0;
            yframe = (yframe + 1) % 4
        delay(0.05)


if __name__ == '__main__':
    run()
