"""Sonic 스프라이트 애니메이션 뷰어와 편집기."""

from pathlib import Path
import argparse
import time

import pico2d as p

BASE_DIR = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1100, 760
VIEW = (24, 202, 1052, 450)
THUMBNAILS = (24, 60, 1052, 122)
BG = (19, 24, 34)
PANEL = (29, 37, 50)
TEXT = (223, 230, 242)


def contains(box, x, y):
    left, bottom, width, height = box
    return left <= x < left + width and bottom <= y < bottom + height


def rectangle(box, color, filled=True):
    x, y, w, h = box
    p.draw_rectangle(x, y, x + w - 1, y + h - 1, *color, filled=filled)


def file_dialog(save=False, **options):
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        function = filedialog.asksaveasfilename if save else filedialog.askopenfilename
        return function(parent=root, **options)
    finally:
        root.destroy()


class App:
    def __init__(self):
        self.running = True
        self.buttons = []
        self.status = "이미지 열기로 스프라이트 시트를 불러올 수 있어."
        self.image_path = BASE_DIR / "sonic-sprite.png"
        self.image = p.load_image(str(self.image_path))
        self.font = p.load_font(str(Path(p.__file__).parent / "data" / "ConsolaMalgun.ttf"), 16)

    def text(self, x, y, value, color=TEXT):
        self.font.draw(x, y, value, color)

    def button(self, box, label, action, active=False):
        rectangle(box, (48, 89, 116) if active else (46, 56, 72))
        x, y, w, h = box
        self.text(x + 9, y + h / 2 - 5, label)
        self.buttons.append((box, action))

    def open_image(self):
        try:
            path = file_dialog(title="스프라이트 이미지 열기", filetypes=[("이미지", "*.png *.jpg *.bmp"), ("모든 파일", "*.*")])
            if path:
                image = p.load_image(path)
                self.image, self.image_path = image, Path(path).resolve()
                self.status = f"이미지: {self.image_path.name}"
        except (OSError, RuntimeError, ValueError) as error:
            self.status = f"이미지 불러오기 실패: {error}"

    def handle_event(self, event):
        if event.type == p.SDL_QUIT:
            self.running = False
        elif event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE:
            self.running = False
        elif event.type == p.SDL_MOUSEBUTTONDOWN and event.button == p.SDL_BUTTON_LEFT:
            for box, action in self.buttons:
                if contains(box, event.x, HEIGHT - 1 - event.y):
                    action()
                    break

    def draw(self):
        self.buttons = []
        p.clear_canvas()
        rectangle((0, 0, WIDTH, HEIGHT), BG)
        rectangle(VIEW, PANEL)
        rectangle(THUMBNAILS, PANEL)
        self.text(24, 724, "SONIC / ANIMATION VIEWER")
        self.button((900, 704, 176, 36), "이미지 열기", self.open_image)
        self.text(24, 32, self.status)

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
