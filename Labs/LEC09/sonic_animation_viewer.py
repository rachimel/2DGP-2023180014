"""Sonic 스프라이트 애니메이션 뷰어와 편집기."""

from pathlib import Path
import argparse
import time
from dataclasses import dataclass, field
from contextlib import contextmanager

import pico2d.pico2d as p

BASE_DIR = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1100, 760
FPS = 60
VIEW = (24, 202, 1052, 450)
THUMBNAILS = (24, 60, 1052, 122)
BG = (19, 24, 34)
PANEL = (29, 37, 50)
TEXT = (223, 230, 242)

# LEC08에서 직접 지정한 Sonic 프레임 좌표. 외부 JSON 없이 실행한다.
DEFAULT_ROWS = (
    ((1,447,29,39,18),(31,447,26,38,14.5),(58,447,28,39,17),(86,447,30,38,17.5),(118,447,30,38,17.5),(150,447,30,38,13.5),(182,447,29,38,11.5),(211,448,29,38,18),(240,448,29,38,18),(270,448,24,32,12),(302,448,29,26,13)),
    ((8,408,26,37,13),(37,408,27,37,13.5),(65,407,31,38,15.5),(97,408,37,37,18.5),(135,410,32,35,16),(170,408,32,38,16),(206,408,26,38,13),(238,408,24,37,12),(263,408,30,37,15),(295,408,36,37,18),(334,409,32,36,16),(370,408,29,38,14.5)),
    ((1,361,33,40,16.5),(39,362,35,39,17.5),(89,362,35,38,17.5),(130,362,34,40,17),(181,362,34,40,17),(228,363,33,39,16.5)),
    ((1,326,29,30,14.5),(35,327,29,31,14.5),(67,327,30,29,15),(98,327,31,29,15.5),(131,327,29,30,14.5),(162,326,29,31,14.5),(193,326,30,29,15),(230,326,31,29,15.5),(268,325,30,30,15)),
    ((1,292,30,27,15),(36,292,29,27,14.5),(70,292,29,27,14.5),(105,292,29,27,14.5),(139,292,29,27,14.5),(174,292,29,27,14.5)),
    ((1,251,29,35,14.5),(36,251,30,35,15),(74,251,31,35,15.5),(111,251,31,36,15.5),(149,251,30,35,15),(186,251,31,36,15.5)),
    ((1,207,29,35,14.5),(36,207,30,35,15),(72,208,39,31,19.5),(123,208,39,32,19.5),(172,208,39,31,19.5),(218,208,38,32,19)),
    ((1,154,24,45,12),(31,154,29,44,14.5),(65,154,20,44,10),(90,155,25,43,12.5),(119,155,25,43,12.5),(149,154,20,44,10),(184,156,40,28,20),(232,157,39,27,19.5)),
    ((1,108,27,38,13.5),(31,110,31,36,15.5),(64,110,31,36,15.5),(99,110,33,38,16.5),(136,110,32,36,16),(176,110,33,36,16.5),(217,110,33,36,16.5),(254,111,33,36,16.5)),
    ((6,56,34,40,17),(49,56,34,43,17),(96,59,23,39,11.5),(125,59,23,39,11.5)),
)


@dataclass
class Frame:
    # rect는 이미지의 왼쪽 아래 기준 (x, y, width, height), pivot은 영역 내부 좌표.
    rect: tuple | None = None
    pivot: tuple = (0.0, 0.0)


@dataclass
class Animation:
    name: str
    frames: list = field(default_factory=lambda: [Frame()])


@dataclass
class Project:
    image_path: Path
    animations: list


def new_project(image_path):
    if image_path.resolve() == (BASE_DIR / "sonic-sprite.png").resolve():
        animations = [Animation(f"동작 {i + 1:02}", [Frame(tuple(row[:4]), (row[4], 0)) for row in rows])
                      for i, rows in enumerate(DEFAULT_ROWS)]
    else:
        animations = [Animation("동작 01")]
    return Project(image_path, animations)


class Player:
    """화면과 독립된 시간 기반 재생 상태."""
    def __init__(self, project):
        self.project = project
        self.index = 0
        self.elapsed = 0.0
        self.finished = False
        self.repeat_five = True
        self.loop = False

    def select(self, index):
        self.index = index % len(self.project.animations)
        self.elapsed = 0.0
        self.finished = False

    @property
    def frame_count(self):
        return len(self.project.animations[self.index].frames)

    @property
    def completed_cycles(self):
        return min(int((self.elapsed + 1e-10) * FPS / self.frame_count), self.repetitions)

    @property
    def repetitions(self):
        return 5 if self.repeat_five else 1

    @property
    def play_duration(self):
        return self.frame_count * self.repetitions / FPS

    @property
    def duration(self):
        return self.play_duration + (1.0 if self.repeat_five else 0.0)

    @property
    def waiting(self):
        return self.repeat_five and self.elapsed + 1e-10 >= self.play_duration and not self.finished

    @property
    def frame_index(self):
        if self.elapsed + 1e-10 >= self.play_duration:
            return self.frame_count - 1
        return int((self.elapsed + 1e-10) * FPS) % self.frame_count

    def update(self, dt):
        if self.finished:
            return
        self.elapsed += max(0, dt)
        if self.loop:
            period = sum(len(a.frames) * self.repetitions / FPS + (1 if self.repeat_five else 0)
                         for a in self.project.animations)
            self.elapsed %= period
        while self.elapsed + 1e-10 >= self.duration:
            duration = self.duration
            if self.index == len(self.project.animations) - 1:
                if not self.loop:
                    self.elapsed = duration
                    self.finished = True
                    break
                self.index = -1
            self.elapsed = max(0, self.elapsed - duration)
            self.index += 1


def contains(box, x, y):
    left, bottom, width, height = box
    return left <= x < left + width and bottom <= y < bottom + height


def rectangle(box, color, filled=True):
    x, y, w, h = box
    p.draw_rectangle(x, y, x + w - 1, y + h - 1, *color, filled=filled)


@contextmanager
def clipped(box):
    previous = p.SDL_Rect()
    enabled = p.SDL_RenderIsClipEnabled(p.renderer)
    p.SDL_RenderGetClipRect(p.renderer, p.ctypes.byref(previous))
    rect = p.to_sdl_rect(*box)
    p.SDL_RenderSetClipRect(p.renderer, p.ctypes.byref(rect))
    try:
        yield
    finally:
        p.SDL_RenderSetClipRect(p.renderer, p.ctypes.byref(previous) if enabled else None)


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
        self.project = new_project(self.image_path)
        self.animation_index = 0
        self.frame_index = 0
        self.player = Player(self.project)
        self.view_scale = 5.0
        self.view_pan = 0.0
        self.font = p.load_font(str(Path(p.__file__).parent / "data" / "ConsolaMalgun.ttf"), 16)

    def text(self, x, y, value, color=TEXT):
        self.font.draw(x, y, value, color)

    @property
    def animation(self):
        return self.project.animations[self.animation_index]

    @property
    def frame(self):
        return self.animation.frames[self.frame_index]

    def draw_frame(self, frame, x, y, scale):
        if frame.rect is None:
            return
        left, bottom, w, h = frame.rect
        px, py = frame.pivot
        self.image.clip_draw(left, bottom, w, h,
                             x + (w / 2 - px) * scale,
                             y + (h / 2 - py) * scale, w * scale, h * scale)

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
                self.project = new_project(self.image_path)
                self.player = Player(self.project)
                self.animation_index = self.frame_index = 0
                self.status = f"이미지: {self.image_path.name}"
        except (OSError, RuntimeError, ValueError) as error:
            self.status = f"이미지 불러오기 실패: {error}"

    def toggle_five(self):
        self.player.repeat_five = not self.player.repeat_five
        self.player.select(self.animation_index)
        self.frame_index = 0

    def toggle_loop(self):
        self.player.loop = not self.player.loop
        if self.player.loop and self.player.finished:
            self.player.select(0)
            self.animation_index = self.frame_index = 0

    def draw_thumbnails(self):
        count = min(7, len(self.project.animations))
        start = -((count - 1) // 2)
        for offset in range(start, start + count):
            index = (self.animation_index + offset) % len(self.project.animations)
            animation = self.project.animations[index]
            box = (WIDTH / 2 - 68 + offset * 146, 70, 136, 102)
            rectangle(box, (39, 49, 65))
            if index == self.animation_index:
                rectangle(box, (255, 215, 64), filled=False)
            frame = animation.frames[0]
            if frame.rect:
                w, h = frame.rect[2:]
                scale = min(2, 110 / w, 62 / h)
                px, py = frame.pivot
                self.draw_frame(frame, box[0] + box[2] / 2 + (px - w / 2) * scale,
                                125 + (py - h / 2) * scale, scale)
            self.text(box[0] + 14, 82, animation.name)
            self.buttons.append((box, lambda i=index: self.select_animation(i)))

    def select_animation(self, index):
        self.player.select(index)
        self.animation_index = self.player.index
        self.frame_index = 0

    def handle_wheel(self, dx, dy, x, y):
        if contains(THUMBNAILS, x, y) and dy:
            self.select_animation(self.animation_index - int(dy))
        elif contains(VIEW, x, y):
            self.view_scale = max(0.5, min(20, self.view_scale * 1.15 ** max(-20, min(20, dy))))
            self.view_pan = max(-2000, min(2000, self.view_pan + dx * 24))

    def handle_event(self, event):
        if event.type == p.SDL_QUIT:
            self.running = False
        elif event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE:
            self.running = False
        elif event.type == p.SDL_KEYDOWN and event.key in (p.SDLK_LEFT, p.SDLK_RIGHT):
            self.select_animation(self.animation_index + (1 if event.key == p.SDLK_RIGHT else -1))
        elif event.type == p.SDL_MOUSEWHEEL:
            mx, my = p.c_int(), p.c_int()
            p.SDL_GetMouseState(p.ctypes.byref(mx), p.ctypes.byref(my))
            self.handle_wheel(event.x, event.y, mx.value, HEIGHT - 1 - my.value)
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
        self.draw_thumbnails()
        with clipped(VIEW):
            p.draw_line(250, 332, 850, 332, 64, 81, 101)
            self.draw_frame(self.frame, WIDTH / 2 + self.view_pan, 332, self.view_scale)
        self.text(40, 628, self.animation.name)
        self.text(40, 600, f"60fps / 프레임 {self.frame_index + 1}/{len(self.animation.frames)} / 완료 {self.player.completed_cycles}회")
        if self.player.waiting:
            self.text(40, 572, "1초 대기 중", (255, 209, 91))
        self.text(24, 724, "SONIC / ANIMATION VIEWER")
        self.button((900, 704, 176, 36), "이미지 열기", self.open_image)
        self.button((24, 663, 245, 30), f"5회 후 대기: {'ON' if self.player.repeat_five else 'OFF'}", self.toggle_five, self.player.repeat_five)
        self.button((280, 663, 220, 30), f"목록 반복: {'ON' if self.player.loop else 'OFF'}", self.toggle_loop, self.player.loop)
        self.text(24, 32, self.status)

    def update(self, dt):
        self.player.update(dt)
        self.animation_index = self.player.index
        self.frame_index = self.player.frame_index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", type=int, default=0, metavar="FRAMES")
    args = parser.parse_args()
    p.open_canvas(WIDTH, HEIGHT)
    if not p.renderer:
        p.renderer = p.SDL_CreateRenderer(p.window, -1, p.SDL_RENDERER_SOFTWARE)
    if not p.renderer:
        p.close_canvas()
        raise RuntimeError("화면 렌더러를 만들 수 없어.")
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
            p.delay(max(0, 1 / FPS - (time.perf_counter() - start)))
    finally:
        p.close_canvas()


if __name__ == "__main__":
    main()
