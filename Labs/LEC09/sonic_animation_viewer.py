"""Sonic 스프라이트 애니메이션 뷰어와 편집기."""

from pathlib import Path
import argparse
import time

import pico2d as p

BASE_DIR = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1100, 760


class App:
    def __init__(self):
        self.running = True

    def handle_event(self, event):
        if event.type == p.SDL_QUIT:
            self.running = False
        elif event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE:
            self.running = False

    def draw(self):
        p.clear_canvas()

    def update(self, dt):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", type=int, default=0, metavar="FRAMES")
    args = parser.parse_args()
    p.open_canvas(WIDTH, HEIGHT)
    p.hide_lattice()
    try:
        app = App()
        previous = time.perf_counter()
        count = 0
        while app.running:
            start = time.perf_counter()
            for event in p.get_events():
                app.handle_event(event)
            app.update(start - previous)
            previous = start
            app.draw()
            p.update_canvas()
            count += 1
            if args.smoke and count >= args.smoke:
                break
            p.delay(max(0, 1 / 60 - (time.perf_counter() - start)))
    finally:
        p.close_canvas()


if __name__ == "__main__":
    main()
