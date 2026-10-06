"""Sonic 스프라이트 애니메이션 뷰어와 편집기."""

from pathlib import Path
import argparse
import time
import json
import os
import tempfile
import math
from dataclasses import dataclass, field
from contextlib import contextmanager

import pico2d.pico2d as p

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PROJECT = BASE_DIR / "sonic_animations.json"
WIDTH, HEIGHT = 1100, 760
DEFAULT_FPS = 60
DISPLAY_FPS = 60
VIEW = (24, 202, 1052, 450)
SHEET = (312, 202, 764, 450)
THUMBNAILS = (24, 60, 1052, 122)
SPEED_INPUT = (560, 663, 126, 30)
SPEED_APPLY = (698, 663, 96, 30)
PLAY_Y = 332
GAME_VIEW = (24, 202, 750, 450)
EVENT_SEARCH = (802, 579, 260, 28)
EVENT_LIST = (802, 473, 260, 100)
ANIMATION_SEARCH = (802, 395, 260, 28)
ANIMATION_LIST = (802, 249, 260, 140)
ROLE_LABELS = {"start": "시작", "idle": "정지", "walk": "걷기", "run_1": "달리기 1단계",
               "run_2": "달리기 2단계", "charge": "스핀 충전",
               "dash": "대시", "jump": "점프 상승", "spring_jump": "스프링 점프", "fall": "일반 하강",
               "spring_fall": "스프링 하강",
               "brake": "제동", "hurt": "피격", "goal": "골"}
BG = (19, 24, 34)
PANEL = (29, 37, 50)
TEXT = (223, 230, 242)

@dataclass
class Frame:
    # rect는 이미지의 왼쪽 아래 기준 (x, y, width, height), pivot은 영역 내부 좌표.
    rect: tuple | None = None
    pivot: tuple = (0.0, 0.0)


@dataclass
class Animation:
    name: str
    frames: list = field(default_factory=lambda: [Frame()])
    fps: float = DEFAULT_FPS


@dataclass
class Project:
    image_path: Path
    animations: list
    event_bindings: dict = field(default_factory=dict)

    def __post_init__(self):
        self.event_bindings.pop("run_3", None)
        legacy_run = self.event_bindings.pop("run", "")
        if legacy_run:
            for event in ("run_1", "run_2"):
                self.event_bindings.setdefault(event, legacy_run)
        for event in ("spring_jump", "fall"):
            self.event_bindings.setdefault(event, self.event_bindings.get("jump", ""))
        self.event_bindings.setdefault("spring_fall", self.event_bindings["fall"])
        for event in ROLE_LABELS:
            self.event_bindings.setdefault(event, "")

    def role_animation(self, role):
        name = self.event_bindings[role]
        return next((a for a in self.animations if a.name == name), self.animations[0])


def new_project(image_path):
    return Project(image_path, [Animation("동작 01")])


def project_document(project, image_size, target):
    try:
        image_reference = Path(os.path.relpath(project.image_path, target.parent)).as_posix()
    except ValueError:
        image_reference = project.image_path.as_posix()
    return {
        "version": 1, "coordinates": "bottom-left",
        "image": {"path": image_reference, "size": list(image_size)},
        "event_bindings": dict(project.event_bindings),
        "animations": [
            {"name": animation.name, "fps": animation.fps, "frames": [
                {"rect": list(frame.rect) if frame.rect else None, "pivot": list(frame.pivot)}
                for frame in animation.frames]}
            for animation in project.animations],
    }


def export_project(project, image_size, target):
    target = Path(target).resolve()
    document = project_document(project, image_size, target)
    # 실패한 저장이 기존 JSON을 손상시키지 않도록 같은 폴더에서 교체한다.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent,
                                         prefix=".sonic-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(document, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validated_fps(value):
    require(type(value) in (int, float) and math.isfinite(value) and 0.1 <= value <= 240,
            "재생 속도는 0.1~240fps 범위의 숫자여야 합니다.")
    return float(value)


def parse_project(document, source):
    require(isinstance(document, dict), "JSON 최상위는 객체여야 합니다.")
    require(document.get("version") == 1, "지원하지 않는 JSON 버전입니다.")
    legacy_fps = validated_fps(document.get("fps", DEFAULT_FPS))
    require(document.get("coordinates") == "bottom-left", "좌표 기준이 일치하지 않습니다.")
    image = document.get("image")
    require(isinstance(image, dict), "이미지 정보가 없습니다.")
    reference, size = image.get("path"), image.get("size")
    require(isinstance(reference, str) and bool(reference.strip()), "이미지 경로가 없습니다.")
    require(isinstance(size, list) and len(size) == 2 and all(type(n) is int and n > 0 for n in size), "이미지 크기가 올바르지 않습니다.")
    rows = document.get("animations")
    require(isinstance(rows, list) and bool(rows), "애니메이션이 하나 이상 필요합니다.")
    animations = []
    for row in rows:
        require(isinstance(row, dict), "동작 정보가 올바르지 않습니다.")
        name, entries = row.get("name"), row.get("frames")
        require(isinstance(name, str) and bool(name.strip()), "동작 이름이 없습니다.")
        require(isinstance(entries, list) and bool(entries), "동작에 프레임이 하나 이상 필요합니다.")
        frames = []
        for entry in entries:
            require(isinstance(entry, dict) and "rect" in entry, "프레임 정보가 올바르지 않습니다.")
            rect, pivot = entry["rect"], entry.get("pivot")
            if rect is not None:
                require(isinstance(rect, list) and len(rect) == 4 and all(type(n) is int for n in rect), "영역은 정수 좌표 4개여야 합니다.")
                x, y, w, h = rect
                require(x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= size[0] and y + h <= size[1], "영역이 이미지 경계를 벗어났습니다.")
            require(isinstance(pivot, list) and len(pivot) == 2 and
                    all(type(n) in (int, float) and math.isfinite(n) for n in pivot), "피봇 좌표가 올바르지 않습니다.")
            frames.append(Frame(tuple(rect) if rect else None, tuple(pivot)))
        animations.append(Animation(name, frames, validated_fps(row.get("fps", legacy_fps))))
    image_path = Path(reference)
    if not image_path.is_absolute():
        image_path = Path(source).resolve().parent / image_path
    role_entries = document.get("event_bindings", document.get("game_roles", {}))
    require(isinstance(role_entries, dict), "플레이 동작 설정이 올바르지 않습니다.")
    roles = {}
    for role, name in role_entries.items():
        if "event_bindings" not in document:
            require(type(name) is int and 0 <= name < len(animations), "이전 플레이 동작 연결이 올바르지 않습니다.")
            name = animations[name].name
        require((role in ROLE_LABELS or role in ("run", "run_3")) and isinstance(name, str), "이벤트 연결은 이벤트 이름과 애니메이션 이름 문자열이어야 합니다.")
        roles[role] = name
    return Project(image_path.resolve(), animations, roles), tuple(size)


def import_project(source):
    source = Path(source).resolve()
    document = json.loads(source.read_text(encoding="utf-8-sig"))
    return parse_project(document, source)


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

    def set_fps(self, value):
        value = validated_fps(value)
        # 현재 프레임의 진행률과 1초 대기의 남은 시간을 보존한다.
        play_elapsed = min(self.elapsed, self.play_duration)
        wait_elapsed = max(0, self.elapsed - self.play_duration)
        self.elapsed = play_elapsed * self.animation.fps / value + wait_elapsed
        self.animation.fps = value

    @property
    def animation(self):
        return self.project.animations[self.index]

    def move_animation(self, source, target, after=False):
        animations = self.project.animations
        require(0 <= source < len(animations) and 0 <= target < len(animations), "동작 위치가 올바르지 않습니다.")
        destination = target + int(after)
        if source < destination:
            destination -= 1
        if destination == source:
            return False
        current = animations[self.index]
        animation = animations.pop(source)
        animations.insert(destination, animation)
        self.index = next(i for i, entry in enumerate(animations) if entry is current)
        return True

    @property
    def frame_count(self):
        return len(self.project.animations[self.index].frames)

    @property
    def completed_cycles(self):
        return min(int((self.elapsed + 1e-10) * self.animation.fps / self.frame_count), self.repetitions)

    @property
    def repetitions(self):
        return 5 if self.repeat_five else 1

    @property
    def play_duration(self):
        return self.frame_count * self.repetitions / self.animation.fps

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
        return int((self.elapsed + 1e-10) * self.animation.fps) % self.frame_count

    def update(self, dt):
        if self.finished:
            return
        self.elapsed += max(0, dt)
        if self.loop:
            period = sum(len(a.frames) * self.repetitions / a.fps + (1 if self.repeat_five else 0)
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


class Game:
    """도형 맵에서 고정 간격으로 입력·이동·충돌·동작을 처리한다."""
    STEP = 1 / 120
    HALF_WIDTH, HEIGHT = 20, 58
    WORLD_WIDTH, GOAL_X = 2600, 2470
    GROUND_FRICTION = 780
    RUN_THRESHOLDS = (220, 280)

    def __init__(self, project):
        self.project = project
        self.x, self.y, self.vx, self.vy = 100.0, 0.0, 0.0, 0.0
        self.facing = 1
        self.grounded = True
        self.spring_jump = False
        self.state = "start"
        self.elapsed = self.accumulator = 0.0
        self.start_time = 0.6
        self.hurt_time = self.invincible = self.dash_time = self.spring_wait = 0.0
        self.charge = 0.0
        self.charging = self.finished = False
        self.hits = 0
        self.keys = set()
        self.obstacles = [(480, 58, 46), (850, 70, 64), (1660, 90, 58), (2050, 65, 45)]
        self.springs = [(1120, 42), (1830, 42)]
        self.spikes = [(1450, 70)]
        self.enemies = [{"x": x, "left": x - 60, "right": x + 60, "direction": 1, "alive": True}
                        for x in (680, 1320, 2240)]

    @property
    def animation(self):
        return self.project.role_animation(self.state)

    @property
    def frame_index(self):
        return int((self.elapsed + 1e-10) * self.animation.fps) % len(self.animation.frames)

    def press(self, key):
        if self.finished:
            return
        self.keys.add(key)
        if self.start_time > 0 or self.hurt_time > 0:
            return
        if key == "jump" and self.grounded:
            self.vy, self.grounded, self.charging = 550, False, False
            self.spring_jump = False
        elif key == "shift" and self.grounded:
            self.charging, self.charge, self.vx = True, 0.0, 0.0

    def release(self, key):
        self.keys.discard(key)
        if key == "shift" and self.charging:
            self.charging = False
            self.vx = self.facing * (400 + self.charge * 220)
            self.dash_time = 0.8

    def stop_input(self):
        self.keys.clear()
        self.charging = False

    def damage(self):
        if self.invincible > 0:
            return
        self.hits += 1
        self.x, self.y, self.vx, self.vy = 100.0, 0.0, 0.0, 0.0
        self.grounded, self.charging = True, False
        self.spring_jump = False
        self.hurt_time, self.invincible, self.dash_time = 0.5, 1.5, 0
        self.keys.clear()

    def update(self, dt):
        self.accumulator += max(0, dt)
        while self.accumulator + 1e-10 >= self.STEP:
            self.accumulator = max(0, self.accumulator - self.STEP)
            self.step(self.STEP)

    def step(self, dt):
        self.elapsed += dt
        for timer in ("start_time", "hurt_time", "invincible", "dash_time", "spring_wait"):
            setattr(self, timer, max(0, getattr(self, timer) - dt))
        if self.finished:
            return
        for enemy in self.enemies:
            if enemy["alive"]:
                enemy["x"] += enemy["direction"] * 60 * dt
                if enemy["x"] >= enemy["right"] or enemy["x"] <= enemy["left"]:
                    enemy["direction"] *= -1
        direction = int("right" in self.keys) - int("left" in self.keys)
        if direction:
            self.facing = direction
        if self.start_time > 0 or self.hurt_time > 0:
            direction = 0
        if self.charging:
            self.charge = min(1, self.charge + dt)
            self.vx = 0
        elif self.dash_time <= 0:
            if direction:
                self.vx = max(-360, min(360, self.vx + direction * 360 * dt))
            else:
                friction = self.GROUND_FRICTION if self.grounded else 520
                self.vx = math.copysign(max(0, abs(self.vx) - friction * dt), self.vx)
        old_x, old_y = self.x, self.y
        self.x = max(self.HALF_WIDTH, min(self.WORLD_WIDTH - self.HALF_WIDTH, self.x + self.vx * dt))
        for x, width, height in self.obstacles:
            if self.x + self.HALF_WIDTH > x and self.x - self.HALF_WIDTH < x + width and self.y < height - 0.01:
                self.x = x - self.HALF_WIDTH if old_x < x else x + width + self.HALF_WIDTH
                self.vx, self.dash_time = 0, 0
        self.vy -= 1400 * dt
        self.y += self.vy * dt
        self.grounded = False
        if self.y <= 0:
            self.y, self.vy, self.grounded = 0, 0, True
        for x, width, height in self.obstacles:
            if self.x + self.HALF_WIDTH > x and self.x - self.HALF_WIDTH < x + width:
                if self.vy <= 0 and old_y >= height - 0.01 and self.y <= height:
                    self.y, self.vy, self.grounded = height, 0, True
        if self.grounded:
            self.spring_jump = False
        for x, width in self.springs:
            if self.spring_wait <= 0 and self.y <= 12 and self.x + self.HALF_WIDTH > x and self.x - self.HALF_WIDTH < x + width:
                self.y, self.vy, self.grounded, self.spring_wait = 12, 720, False, 0.35
                self.charging = False
                self.spring_jump = True
        for x, width in self.spikes:
            if self.y < 26 and self.x + self.HALF_WIDTH > x and self.x - self.HALF_WIDTH < x + width:
                self.damage()
        for enemy in self.enemies:
            if enemy["alive"] and abs(self.x - enemy["x"]) < self.HALF_WIDTH + 18 and self.y < 36:
                if self.dash_time > 0 or (self.vy < 0 and old_y >= 30):
                    enemy["alive"] = False
                    if self.vy < 0:
                        self.vy, self.grounded = 350, False
                        self.spring_jump = False
                else:
                    self.damage()
        if self.x >= self.GOAL_X and self.grounded:
            self.finished = True
            self.vx = 0
        if self.vy < 0:
            air_state = "spring_fall" if self.spring_jump else "fall"
        else:
            air_state = "spring_jump" if self.spring_jump else "jump"
        state = ("goal" if self.finished else "hurt" if self.hurt_time > 0 else "start" if self.start_time > 0
                 else "charge" if self.charging else air_state if not self.grounded
                 else "dash" if self.dash_time > 0 else "brake" if not direction and abs(self.vx) > 5
                 else f"run_{sum(abs(self.vx) >= speed for speed in self.RUN_THRESHOLDS)}" if abs(self.vx) >= self.RUN_THRESHOLDS[0]
                 else "walk" if abs(self.vx) > 5 else "idle")
        if state != self.state:
            self.state, self.elapsed = state, 0.0


def contains(box, x, y):
    left, bottom, width, height = box
    return left <= x < left + width and bottom <= y < bottom + height


def selection_rect(start, end, width, height):
    ax, ay = start
    bx, by = end
    ax, bx = (max(0, min(width - 1, int(v))) for v in (ax, bx))
    ay, by = (max(0, min(height - 1, int(v))) for v in (ay, by))
    return (min(ax, bx), min(ay, by), abs(ax - bx) + 1, abs(ay - by) + 1)


def moved_rect(rect, dx, dy, width, height):
    x, y, w, h = rect
    return (max(0, min(width - w, x + int(dx))),
            max(0, min(height - h, y + int(dy))), w, h)


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


def app_events():
    """pico2d 기본 이벤트에 한글 검색용 SDL 텍스트 입력을 추가한다."""
    raw = p.SDL_Event()
    events = []
    while p.SDL_PollEvent(p.ctypes.byref(raw)):
        event = p.Event(raw.type)
        if raw.type in (p.SDL_TEXTINPUT, p.SDL_TEXTEDITING):
            event.text = bytes(raw.text.text if raw.type == p.SDL_TEXTINPUT else raw.edit.text).decode("utf-8")
        elif raw.type in (p.SDL_KEYDOWN, p.SDL_KEYUP):
            if raw.key.repeat:
                continue
            event.key = raw.key.keysym.sym
        elif raw.type == p.SDL_MOUSEMOTION:
            event.x, event.y = raw.motion.x, raw.motion.y
        elif raw.type in (p.SDL_MOUSEBUTTONDOWN, p.SDL_MOUSEBUTTONUP):
            event.button, event.x, event.y = raw.button.button, raw.button.x, raw.button.y
        elif raw.type == p.SDL_MOUSEWHEEL:
            event.x, event.y = raw.wheel.x, raw.wheel.y
            if raw.wheel.direction == p.SDL_MOUSEWHEEL_FLIPPED:
                event.x, event.y = -event.x, -event.y
        elif raw.type != p.SDL_QUIT:
            continue
        events.append(event)
    return events


class App:
    def __init__(self):
        self.running = True
        self.buttons = []
        self.status = "기본 sonic_animations.json 설정을 불러왔습니다."
        self.project, image_size = import_project(DEFAULT_PROJECT)
        self.image_path = self.project.image_path
        self.image = p.load_image(str(self.image_path))
        require((self.image.w, self.image.h) == image_size, "기본 JSON의 이미지 크기가 원본과 다릅니다.")
        self.animation_index = 0
        self.frame_index = 0
        self.player = Player(self.project)
        self.view_scale = 5.0
        self.view_pan = 0.0
        self.screen = "viewer"
        self.editor_scale = min((SHEET[2] - 40) / self.image.w, (SHEET[3] - 40) / self.image.h)
        self.editor_pan = [0.0, 0.0]
        self.region_mode = False
        self.drag = None
        self.draft_rect = None
        self.thumbnail_drag = None
        self.onion = True
        self.grid = True
        self.grid_size = 8
        self.mouse_position = (-1, -1)
        self.json_path = DEFAULT_PROJECT
        self.fps_editing = False
        self.fps_select_all = False
        self.fps_text = f"{self.animation.fps:g}"
        self.fps_target = None
        self.game = Game(self.project)
        self.play_paused = False
        self.binding_event = "start"
        self.search_focus = None
        self.search_queries = {"event": "", "animation": ""}
        self.search_offsets = {"event": 0, "animation": 0}
        self.search_composition = ""
        self.font = p.load_font(str(Path(p.__file__).parent / "data" / "ConsolaMalgun.ttf"), 16)

    def text(self, x, y, value, color=TEXT):
        self.font.draw(x, y, value, color)

    @property
    def animation(self):
        return self.project.animations[self.animation_index]

    @property
    def frame(self):
        return self.animation.frames[self.frame_index]

    @property
    def speed_animation(self):
        if self.screen == "play":
            return self.project.role_animation(self.binding_event)
        return self.animation

    @property
    def speed_boxes(self):
        if self.screen == "editor":
            return (40, 208, 140, 26), (184, 208, 104, 26)
        return SPEED_INPUT, SPEED_APPLY

    def draw_frame(self, frame, x, y, scale, flip=False):
        if frame.rect is None:
            return
        left, bottom, w, h = frame.rect
        px, py = frame.pivot
        self.image.clip_composite_draw(left, bottom, w, h, 0, 'h' if flip else '',
                             x + (px - w / 2 if flip else w / 2 - px) * scale,
                             y + (h / 2 - py) * scale, w * scale, h * scale)

    def button(self, box, label, action, active=False):
        rectangle(box, (48, 89, 116) if active else (46, 56, 72))
        x, y, w, h = box
        self.text(x + 9, y + h / 2 - 5, label)
        self.buttons.append((box, action))

    def tab(self, box, label, screen):
        active = self.screen == screen
        rectangle(box, PANEL if active else (24, 30, 42))
        x, y, w, h = box
        self.text(x + w / 2 - 16, y + h / 2 - 5, label)
        if active:
            rectangle((x, y, w, 3), (255, 215, 64))
        self.buttons.append((box, lambda: self.set_screen(screen)))

    def open_image(self):
        try:
            path = file_dialog(title="스프라이트 이미지 열기", filetypes=[("이미지", "*.png *.jpg *.bmp"), ("모든 파일", "*.*")])
            if path:
                image = p.load_image(path)
                self.image, self.image_path = image, Path(path).resolve()
                self.project = new_project(self.image_path)
                self.player = Player(self.project)
                self.animation_index = self.frame_index = 0
                self.cancel_drag()
                self.editor_scale = min((SHEET[2] - 40) / image.w, (SHEET[3] - 40) / image.h)
                self.editor_pan = [0.0, 0.0]
                self.region_mode = False
                self.json_path = None
                self.cancel_fps_edit()
                self.reset_play()
                self.status = f"이미지: {self.image_path.name}"
        except (OSError, RuntimeError, ValueError) as error:
            self.status = f"이미지 불러오기 실패: {error}"

    def save_json(self):
        try:
            path = file_dialog(save=True, title="편집 데이터 JSON 저장", defaultextension=".json",
                               initialfile=self.json_path.name if self.json_path else "sonic_animations.json",
                               filetypes=[("JSON", "*.json")])
            if path:
                export_project(self.project, (self.image.w, self.image.h), path)
                self.json_path = Path(path).resolve()
                self.status = f"JSON 저장 완료: {self.json_path.name}"
        except (OSError, ValueError, RuntimeError) as error:
            self.status = f"JSON 저장 실패: {error}"

    def import_from(self, path):
        project, size = import_project(path)
        image = p.load_image(str(project.image_path))
        require((image.w, image.h) == size, "원본 이미지 크기가 JSON과 다릅니다.")
        # 데이터와 이미지가 모두 유효할 때만 현재 편집 상태를 교체한다.
        self.cancel_drag()
        self.image, self.image_path, self.project = image, project.image_path, project
        self.player = Player(project)
        self.animation_index = self.frame_index = 0
        self.editor_scale = min((SHEET[2] - 40) / image.w, (SHEET[3] - 40) / image.h)
        self.editor_pan = [0.0, 0.0]
        self.region_mode = False
        self.json_path = Path(path).resolve()
        self.cancel_fps_edit()
        self.reset_play()
        self.status = f"JSON 불러오기 완료: {self.json_path.name}"

    def load_json(self):
        try:
            path = file_dialog(title="편집 데이터 JSON 열기", filetypes=[("JSON", "*.json")])
            if path:
                self.import_from(path)
        except (OSError, ValueError, RuntimeError) as error:
            self.status = f"JSON 불러오기 실패: {error}"

    def toggle_five(self):
        self.player.repeat_five = not self.player.repeat_five
        self.player.select(self.animation_index)
        self.frame_index = 0

    def start_fps_edit(self):
        self.focus_search(None)
        self.game.stop_input()
        self.fps_editing = True
        self.fps_select_all = True
        self.fps_target = self.speed_animation
        self.fps_text = f"{self.fps_target.fps:g}"

    def cancel_fps_edit(self):
        self.fps_editing = False
        self.fps_select_all = False
        self.fps_target = None
        self.fps_text = f"{self.speed_animation.fps:g}"

    def apply_fps(self):
        target = self.fps_target or self.speed_animation
        old_fps = target.fps
        try:
            value = validated_fps(float(self.fps_text) if self.fps_editing else target.fps)
        except ValueError:
            self.fps_editing = True
            self.status = "재생 속도는 0.1~240fps 범위의 숫자로 입력하세요."
            return
        if self.player.animation is target:
            self.player.set_fps(value)
        else:
            target.fps = value
        if self.screen == "play":
            if self.game.animation is target:
                self.game.elapsed *= old_fps / value
            self.sync_game()
        elif self.screen == "viewer":
            self.frame_index = self.player.frame_index
        self.cancel_fps_edit()
        self.status = f"{target.name} 재생 속도 적용: {value:g}fps"

    def handle_fps_key(self, key):
        if key in (p.SDLK_RETURN, p.SDLK_KP_ENTER):
            self.apply_fps()
            return
        if key == p.SDLK_ESCAPE:
            self.cancel_fps_edit()
            return
        if key in (p.SDLK_BACKSPACE, p.SDLK_DELETE):
            self.fps_text = "" if self.fps_select_all or key == p.SDLK_DELETE else self.fps_text[:-1]
            self.fps_select_all = False
            return
        digits = {p.SDLK_KP_0: "0", **{p.SDLK_KP_1 + i: str(i + 1) for i in range(9)}}
        character = chr(key) if ord("0") <= key <= ord("9") else digits.get(key)
        if key in (p.SDLK_PERIOD, p.SDLK_KP_PERIOD):
            character = "."
        if character is not None:
            text = "" if self.fps_select_all else self.fps_text
            if len(text) < 8 and (character != "." or "." not in text):
                self.fps_text = text + character
                self.fps_select_all = False

    def draw_speed_control(self):
        input_box, apply_box = self.speed_boxes
        if self.screen == "editor":
            self.text(40, 238, f"동작 속도: {self.speed_animation.name[:7]}")
        else:
            self.text(516, 675, "FPS")
        rectangle(input_box, (15, 20, 29))
        rectangle(input_box, (255, 215, 64) if self.fps_editing else (86, 103, 124), filled=False)
        x, y, w, h = input_box
        if self.fps_editing and self.fps_select_all:
            rectangle((x + 7, y + 5, max(8, len(self.fps_text) * 9), 21), (62, 93, 132))
        value = self.fps_text if self.fps_editing else f"{self.speed_animation.fps:g}"
        self.text(x + 9, y + h / 2 - 5, value + ("_" if self.fps_editing and not self.fps_select_all else ""))
        self.buttons.append((input_box, self.start_fps_edit))
        self.button(apply_box, "적용", self.apply_fps, self.fps_editing)
        if self.screen != "editor":
            self.text(812, 675, f"{self.speed_animation.name[:7]} · Enter 적용", (153, 171, 196))

    def toggle_loop(self):
        self.player.loop = not self.player.loop
        if self.player.loop and self.player.finished:
            self.player.select(0)
            self.animation_index = self.frame_index = 0

    def thumbnail_items(self):
        count = min(7, len(self.project.animations))
        start = -((count - 1) // 2)
        anchor = self.thumbnail_drag["anchor"] if self.thumbnail_drag else self.animation_index
        return [((anchor + offset) % len(self.project.animations),
                 (WIDTH / 2 - 68 + offset * 146, 70, 136, 102))
                for offset in range(start, start + count)]

    def draw_thumbnail(self, index, box, color=(39, 49, 65)):
        animation = self.project.animations[index]
        rectangle(box, color)
        frame = animation.frames[0]
        if frame.rect:
            w, h = frame.rect[2:]
            scale = min(2, 110 / w, 62 / h)
            px, py = frame.pivot
            self.draw_frame(frame, box[0] + box[2] / 2 + (px - w / 2) * scale,
                            box[1] + 55 + (py - h / 2) * scale, scale)
        self.text(box[0] + 14, box[1] + 12, animation.name[:7])

    def draw_thumbnails(self):
        drag = self.thumbnail_drag
        drop_box = None
        with clipped(THUMBNAILS):
            for index, box in self.thumbnail_items():
                self.draw_thumbnail(index, box)
                if index == self.animation_index:
                    rectangle(box, (255, 215, 64), filled=False)
                if drag and drag["moving"] and drag["target"] and index == drag["target"][0]:
                    drop_box = box
            if drag and drag["moving"]:
                x, y = drag["position"]
                box = (x - 68, y - 51, 136, 102)
                self.image.opacify(0.65)
                try:
                    self.draw_thumbnail(drag["source"], box, (46, 74, 89, 220))
                    rectangle(box, (98, 221, 224), filled=False)
                finally:
                    self.image.opacify(1.0)
            if drop_box:
                marker_x = drop_box[0] + drop_box[2] + 3 if drag["target"][1] else drop_box[0] - 5
                rectangle((marker_x, drop_box[1], 3, drop_box[3]), (98, 221, 224))

    def hit_thumbnail(self, x, y):
        return next((i for i, box in self.thumbnail_items() if contains(box, x, y)), None)

    def thumbnail_drop_target(self, x, y):
        if not contains(THUMBNAILS, x, y):
            return None
        index, box = min(self.thumbnail_items(), key=lambda item: abs(x - (item[1][0] + item[1][2] / 2)))
        return index, x >= box[0] + box[2] / 2

    def start_thumbnail_drag(self, index, x, y):
        self.cancel_drag()
        self.thumbnail_drag = {"source": index, "start": (x, y), "position": (x, y),
                               "anchor": self.animation_index, "moving": False, "target": None}

    def update_thumbnail_drag(self, x, y):
        drag = self.thumbnail_drag
        drag["position"] = (x, y)
        sx, sy = drag["start"]
        if abs(x - sx) + abs(y - sy) >= 6:
            drag["moving"] = True
        if drag["moving"]:
            drag["target"] = self.thumbnail_drop_target(x, y)

    def finish_thumbnail_drag(self, x, y):
        self.update_thumbnail_drag(x, y)
        drag = self.thumbnail_drag
        hit = self.hit_thumbnail(x, y)
        self.thumbnail_drag = None
        if not drag["moving"]:
            if hit == drag["source"]:
                self.select_animation(hit)
        elif drag["target"]:
            target, after = drag["target"]
            if self.player.move_animation(drag["source"], target, after):
                self.animation_index = self.player.index
                self.status = "애니메이션 순서 변경 완료 · JSON 저장으로 보관할 수 있습니다."

    def select_animation(self, index):
        self.cancel_drag()
        self.player.select(index)
        self.animation_index = self.player.index
        self.frame_index = 0

    def handle_wheel(self, dx, dy, x, y):
        if self.screen == "play":
            for kind, box, count in (("event", EVENT_LIST, 4), ("animation", ANIMATION_LIST, 5)):
                if contains(box, x, y):
                    limit = max(0, len(self.search_results(kind)) - count)
                    self.search_offsets[kind] = max(0, min(limit, self.search_offsets[kind] - int(dy)))
            return
        if self.thumbnail_drag:
            if contains(THUMBNAILS, x, y) and dy:
                self.thumbnail_drag["anchor"] = (self.thumbnail_drag["anchor"] - int(dy)) % len(self.project.animations)
                self.update_thumbnail_drag(x, y)
            return
        if contains(THUMBNAILS, x, y) and dy:
            self.select_animation(self.animation_index - int(dy))
        elif contains(VIEW, x, y):
            factor = 1.15 ** max(-20, min(20, dy))
            if self.screen in ("viewer", "play"):
                self.view_scale = max(0.5, min(20, self.view_scale * factor))
                self.view_pan = max(-2000, min(2000, self.view_pan + dx * 24))
            elif contains(SHEET, x, y):
                self.cancel_drag()
                ox, oy = self.sheet_origin()
                # 정수 픽셀로 반올림하지 않고 커서 아래 시트 좌표를 보존한다.
                anchor_x = (x - ox) / self.editor_scale
                anchor_y = (y - oy) / self.editor_scale
                self.editor_scale = max(0.25, min(20, self.editor_scale * factor))
                nx, ny = self.sheet_origin()
                self.editor_pan[0] += x - (nx + anchor_x * self.editor_scale) + dx * 24
                self.editor_pan[1] += y - (ny + anchor_y * self.editor_scale)
                self.mouse_position = (x, y)

    def set_screen(self, screen):
        if self.screen == screen:
            return
        self.cancel_drag()
        self.focus_search(None)
        self.cancel_fps_edit()
        self.screen = screen
        self.player.select(self.animation_index)
        self.frame_index = 0
        self.game.stop_input()

        if screen == "play":
            self.reset_play()

    def toggle_play_pause(self):
        self.play_paused = not self.play_paused
        self.game.stop_input()

    def reset_play(self):
        self.game = Game(self.project)
        self.play_paused = False
        if self.screen == "play":
            self.sync_game()

    def sync_game(self):
        self.animation_index = next(i for i, a in enumerate(self.project.animations) if a is self.game.animation)
        self.player.index = self.animation_index
        self.frame_index = self.game.frame_index

    def draw_game_events(self):
        self.text(34, 158, "오른쪽 사이드바에서 이벤트 선택 후 애니메이션 클릭 · JSON 저장 가능")
        event = self.game.state
        name = self.project.event_bindings[event]
        self.text(34, 124, f'현재 이벤트: "{event}" -> "{name}"', (255, 215, 64))
        missing = not any(a.name == name for a in self.project.animations)
        self.text(34, 90, "연결한 이름을 찾을 수 없어 첫 동작을 표시합니다." if missing else "입력·충돌 이벤트에 따라 연결된 동작을 자동 재생합니다.")

    def search_results(self, kind):
        query = self.search_queries[kind].strip().casefold()
        if kind == "event":
            return [e for e in ROLE_LABELS if query in f"{e} {ROLE_LABELS[e]} {self.project.event_bindings[e]}".casefold()]
        return [a.name for a in self.project.animations if query in a.name.casefold()]

    def focus_search(self, kind):
        self.search_focus = kind
        self.search_composition = ""
        if kind:
            self.cancel_fps_edit()
            self.game.stop_input()
            box = EVENT_SEARCH if kind == "event" else ANIMATION_SEARCH
            rect = p.SDL_Rect(int(box[0]), int(HEIGHT - box[1] - box[3]), int(box[2]), int(box[3]))
            p.SDL_SetTextInputRect(p.ctypes.byref(rect))
            p.SDL_StartTextInput()
        else:
            p.SDL_StopTextInput()

    def choose_binding_event(self, event):
        self.cancel_fps_edit()
        self.binding_event = event

    def bind_animation(self, name):
        self.game.stop_input()
        if sum(a.name == name for a in self.project.animations) != 1:
            self.status = "동작 이름이 중복되어 있습니다. 고유한 이름으로 연결하세요."
            return
        self.project.event_bindings[self.binding_event] = name
        self.sync_game()
        self.status = f'"{self.binding_event}" -> "{name}" 연결 변경 · JSON 저장으로 보관하세요.'

    def draw_binding_sidebar(self):
        rectangle((786, 202, 290, 450), (24, 30, 42))
        self.text(802, 628, "이벤트 연결")
        self.text(802, 611, "이벤트 / 한글명 / 연결 이름 검색", (153, 171, 196))
        for kind, box in (("event", EVENT_SEARCH), ("animation", ANIMATION_SEARCH)):
            rectangle(box, BG)
            rectangle(box, (255, 215, 64) if self.search_focus == kind else (86, 103, 124), filled=False)
            value = self.search_queries[kind]
            if self.search_focus == kind:
                value += self.search_composition + "_"
            with clipped(box):
                self.text(box[0] + 8, box[1] + 9, value or "검색어 입력")
            self.buttons.append((box, lambda k=kind: self.focus_search(k)))
        for kind, box, count, height in (("event", EVENT_LIST, 4, 25), ("animation", ANIMATION_LIST, 5, 28)):
            results = self.search_results(kind)
            offset = min(self.search_offsets[kind], max(0, len(results) - count))
            self.search_offsets[kind] = offset
            with clipped(box):
                for i, value in enumerate(results[offset:offset + count]):
                    row = (box[0], box[1] + box[3] - (i + 1) * height, box[2], height - 2)
                    if kind == "event":
                        label = f"{value} · {ROLE_LABELS[value]}"
                        action = lambda e=value: self.choose_binding_event(e)
                        active = value == self.binding_event
                    else:
                        label = value
                        action = lambda n=value: self.bind_animation(n)
                        active = value == self.project.event_bindings[self.binding_event]
                    self.button(row, label, action, active)
                if not results:
                    self.text(box[0] + 8, box[1] + box[3] - 22, "검색 결과 없음")
        with clipped((802, 429, 260, 40)):
            self.text(802, 452, f"선택: {self.binding_event} / {ROLE_LABELS[self.binding_event]}")
            self.text(802, 432, f"연결: {self.project.event_bindings[self.binding_event]}")
        self.text(802, 225, "목록 휠 이동 · 클릭 즉시 연결", (153, 171, 196))

    def draw_play(self):
        game = self.game
        camera = max(0, min(game.WORLD_WIDTH - GAME_VIEW[2], game.x - GAME_VIEW[2] * .42))
        sx = lambda x: GAME_VIEW[0] + x - camera
        with clipped(GAME_VIEW):
            rectangle((GAME_VIEW[0], GAME_VIEW[1], GAME_VIEW[2], PLAY_Y - GAME_VIEW[1]), (35, 48, 58))
            p.draw_line(GAME_VIEW[0], PLAY_Y, GAME_VIEW[0] + GAME_VIEW[2] - 1, PLAY_Y, 126, 179, 144)
            for x, w, h in game.obstacles:
                rectangle((sx(x), PLAY_Y, w, h), (102, 113, 132))
            for x, w in game.springs:
                rectangle((sx(x), PLAY_Y, w, 12), (246, 205, 74))
                self.text(sx(x) - 12, PLAY_Y - 28, "스프링")
            for x, w in game.spikes:
                for offset in range(0, w, 14):
                    p.draw_line(sx(x + offset), PLAY_Y, sx(x + offset + 7), PLAY_Y + 26, 246, 113, 91)
                    p.draw_line(sx(x + offset + 7), PLAY_Y + 26, sx(x + offset + 14), PLAY_Y, 246, 113, 91)
            for enemy in game.enemies:
                if enemy["alive"]:
                    rectangle((sx(enemy["x"]) - 18, PLAY_Y, 36, 36), (220, 83, 91))
                    rectangle((sx(enemy["x"]) - 10, PLAY_Y + 23, 6, 6), (255, 255, 255))
            for x, label, color in ((100, "시작", (114, 214, 151)), (game.GOAL_X, "골", (91, 209, 231))):
                rectangle((sx(x), PLAY_Y, 3, 110), color)
                rectangle((sx(x), PLAY_Y + 82, 44, 28), color)
                self.text(sx(x) - 8, PLAY_Y + 124, label)
            if not game.invincible or int(game.invincible * 12) % 2 == 0:
                if self.frame.rect:
                    self.draw_frame(self.frame, sx(game.x), PLAY_Y + game.y, 2, game.facing < 0)
                else:
                    rectangle((sx(game.x) - 20, PLAY_Y + game.y, 40, 58), (83, 150, 247))
        self.text(40, 628, f"PLAY / {ROLE_LABELS[game.state]} / {self.animation.name}")
        self.text(40, 600, f"이동 속도 {abs(game.vx):.0f} · 피격 {game.hits}회 · {game.animation.fps:g}fps")
        if game.finished:
            self.text(40, 572, "골 도착! R 또는 다시 시작으로 재도전", (255, 215, 64))
        elif game.charging:
            self.text(40, 572, f"스핀 충전 {game.charge * 100:.0f}% · Shift를 놓으면 대시")
        self.draw_binding_sidebar()

    def select_frame(self, step):
        self.cancel_drag()
        self.frame_index = (self.frame_index + step) % len(self.animation.frames)

    def add_frame(self):
        self.cancel_drag()
        self.animation.frames.insert(self.frame_index + 1, Frame())
        self.frame_index += 1
        self.player.select(self.animation_index)

    def remove_frame(self):
        self.cancel_drag()
        if len(self.animation.frames) == 1:
            self.animation.frames[0] = Frame()
        else:
            self.animation.frames.pop(self.frame_index)
            self.frame_index = min(self.frame_index, len(self.animation.frames) - 1)
        self.player.select(self.animation_index)

    def add_animation(self):
        self.project.animations.append(Animation(f"동작 {len(self.project.animations) + 1:02}"))
        self.select_animation(len(self.project.animations) - 1)

    def remove_animation(self):
        if len(self.project.animations) == 1:
            self.project.animations[0] = Animation("동작 01")
        else:
            self.project.animations.pop(self.animation_index)
        self.select_animation(min(self.animation_index, len(self.project.animations) - 1))

    def draw_editor_controls(self):
        self.draw_speed_control()
        self.button((24, 663, 110, 30), "이전 프레임", lambda: self.select_frame(-1))
        self.button((144, 663, 110, 30), "다음 프레임", lambda: self.select_frame(1))
        self.button((264, 663, 130, 30), "프레임 추가", self.add_frame)
        self.button((404, 663, 130, 30), "프레임 제거", self.remove_frame)
        self.button((544, 663, 125, 30), "동작 추가", self.add_animation)
        self.button((679, 663, 125, 30), "동작 제거", self.remove_animation)
        self.button((814, 663, 262, 30), f"어니언 스킨: {'ON' if self.onion else 'OFF'}", self.toggle_onion, self.onion)
        self.text(40, 628, f"{self.animation.name[:6]} / 프레임 {self.frame_index + 1}/{len(self.animation.frames)}")
        self.button((40, 584, 230, 30), f"[{'x' if self.region_mode else ' '}] 영역 지정 모드", self.toggle_region, self.region_mode)
        self.text(40, 552, f"영역: {self.frame.rect or '미지정'}")
        self.text(40, 526, f"피봇: {self.frame.pivot}")
        self.button((40, 484, 140, 30), f"[{'x' if self.grid else ' '}] 격자 {self.grid_size}px", self.toggle_grid, self.grid)
        self.button((184, 484, 40, 30), "-", lambda: self.resize_grid(-1))
        self.button((228, 484, 40, 30), "+", lambda: self.resize_grid(1))

    def toggle_grid(self):
        self.grid = not self.grid

    def grid_step(self):
        return self.grid_size

    def resize_grid(self, direction):
        self.grid_size = max(1, min(256, self.grid_size * 2 if direction > 0 else self.grid_size // 2))

    def hovered_grid_cell(self):
        x, y = self.mouse_position
        if not self.grid or self.screen != "editor" or not contains(SHEET, x, y):
            return None
        px, py = self.source_point(x, y)
        if not contains((0, 0, self.image.w, self.image.h), px, py):
            return None
        step = self.grid_size
        left, bottom = px // step * step, py // step * step
        return (left, bottom, min(step, self.image.w - left), min(step, self.image.h - bottom))

    def draw_grid(self):
        if not self.grid:
            return
        ox, oy = self.sheet_origin()
        scale, step = self.editor_scale, self.grid_step()
        left, bottom, width, height = SHEET
        # 시트 픽셀에 맞추고, 화면에 보이는 선만 그린다.
        start_x = max(0, math.ceil((left - ox) / (scale * step)) * step)
        end_x = min(self.image.w, math.floor((left + width - ox) / scale))
        start_y = max(0, math.ceil((bottom - oy) / (scale * step)) * step)
        end_y = min(self.image.h, math.floor((bottom + height - oy) / scale))
        for ix in range(start_x, end_x + 1, step):
            alpha = 105 if ix % (step * 8) == 0 else 55
            p.draw_line(ox + ix * scale, oy, ox + ix * scale, oy + self.image.h * scale,
                        140, 166, 192, alpha)
        for iy in range(start_y, end_y + 1, step):
            alpha = 105 if iy % (step * 8) == 0 else 55
            p.draw_line(ox, oy + iy * scale, ox + self.image.w * scale, oy + iy * scale,
                        140, 166, 192, alpha)
        cell = self.hovered_grid_cell()
        if cell:
            rectangle(self.screen_rect(cell), (91, 209, 231, 65))
            rectangle(self.screen_rect(cell), (91, 209, 231), filled=False)

    def toggle_region(self):
        self.cancel_drag()
        self.region_mode = not self.region_mode

    def toggle_onion(self):
        self.onion = not self.onion

    def draw_onion(self):
        if not self.onion:
            return
        for index, color in ((self.frame_index - 1, (240, 133, 110)),
                             (self.frame_index + 1, (119, 202, 168))):
            if not 0 <= index < len(self.animation.frames):
                continue
            frame = self.animation.frames[index]
            if frame.rect:
                box = self.screen_rect(frame.rect)
                rectangle(box, (*color, 45))
                rectangle(box, (*color, 110), filled=False)

    def draw_editor_preview(self):
        box = (40, 252, 248, 222)
        rectangle(box, (24, 30, 42))
        with clipped(box):
            if self.onion:
                self.image.opacify(0.25)
                try:
                    for index in (self.frame_index - 1, self.frame_index + 1):
                        if 0 <= index < len(self.animation.frames):
                            self.draw_frame(self.animation.frames[index], 164, 288, 3)
                finally:
                    self.image.opacify(1.0)
            self.draw_frame(self.frame, 164, 288, 3)
        self.text(54, 449, "피봇 기준 미리보기")

    def cancel_drag(self):
        self.drag = None
        self.draft_rect = None
        self.thumbnail_drag = None

    def source_point(self, x, y):
        ox, oy = self.sheet_origin()
        return (int((x - ox) // self.editor_scale), int((y - oy) // self.editor_scale))

    def screen_rect(self, rect):
        ox, oy = self.sheet_origin()
        x, y, w, h = rect
        return (ox + x * self.editor_scale, oy + y * self.editor_scale,
                w * self.editor_scale, h * self.editor_scale)

    def editor_down(self, button, x, y):
        if self.screen != "editor" or not contains(SHEET, x, y):
            return
        point = self.source_point(x, y)
        if button == p.SDL_BUTTON_RIGHT and self.frame.rect:
            self.cancel_drag()
            rx, ry, w, h = self.frame.rect
            self.frame.pivot = (max(0, min(w, point[0] - rx)), max(0, min(h, point[1] - ry)))
            self.status = f"피봇 설정: {self.frame.pivot}"
            return
        if button == p.SDL_BUTTON_MIDDLE:
            self.drag = {"kind": "pan", "start": (x, y), "pan": self.editor_pan.copy()}
            return
        if button == p.SDL_BUTTON_LEFT and (self.region_mode or self.frame.rect is None):
            if not contains((0, 0, self.image.w, self.image.h), *point):
                return
            self.drag = {"kind": "create", "start": point}
            self.draft_rect = selection_rect(point, point, self.image.w, self.image.h)
        elif button == p.SDL_BUTTON_LEFT and self.frame.rect and contains(self.frame.rect, *point):
            self.drag = {"kind": "move", "start": point, "rect": self.frame.rect}
            self.draft_rect = self.frame.rect

    def editor_motion(self, x, y):
        if self.drag and self.drag["kind"] == "create":
            self.draft_rect = selection_rect(self.drag["start"], self.source_point(x, y), self.image.w, self.image.h)
        elif self.drag and self.drag["kind"] == "move":
            sx, sy = self.drag["start"]
            px, py = self.source_point(x, y)
            self.draft_rect = moved_rect(self.drag["rect"], px - sx, py - sy, self.image.w, self.image.h)
        elif self.drag and self.drag["kind"] == "pan":
            sx, sy = self.drag["start"]
            ox, oy = self.drag["pan"]
            self.editor_pan = [ox + x - sx, oy + y - sy]

    def editor_up(self, button, x, y):
        if button == p.SDL_BUTTON_MIDDLE and self.drag and self.drag["kind"] == "pan":
            self.editor_motion(x, y)
            self.cancel_drag()
            return
        if button == p.SDL_BUTTON_LEFT and self.drag:
            if self.drag["kind"] == "pan":
                return
            self.editor_motion(x, y)
            if self.draft_rect:
                self.frame.rect = self.draft_rect
                if self.drag["kind"] == "create":
                    self.frame.pivot = (self.draft_rect[2] / 2, 0)
                self.region_mode = False
                self.status = "영역 지정 완료"
            self.cancel_drag()

    def remove_region(self):
        self.cancel_drag()
        self.frame.rect = None
        self.frame.pivot = (0.0, 0.0)
        self.status = "현재 프레임의 참조 영역 제거 완료"

    def sheet_origin(self):
        return (SHEET[0] + (SHEET[2] - self.image.w * self.editor_scale) / 2 + self.editor_pan[0],
                SHEET[1] + (SHEET[3] - self.image.h * self.editor_scale) / 2 + self.editor_pan[1])

    def draw_editor(self):
        x, y = self.sheet_origin()
        with clipped(SHEET):
            self.image.draw_to_origin(x, y, self.image.w * self.editor_scale, self.image.h * self.editor_scale)
            self.draw_grid()
            self.draw_onion()
            rect = self.draft_rect if self.drag and self.drag["kind"] != "pan" else self.frame.rect
            if rect:
                box = self.screen_rect(rect)
                if not self.drag or self.drag["kind"] == "pan":
                    rectangle(box, (61, 175, 237, 65))
                rectangle(box, (255, 215, 64), filled=False)
                if not self.drag or self.drag["kind"] != "create":
                    rx, ry, _, _ = rect
                    px, py = self.frame.pivot
                    cx, cy = x + (rx + px) * self.editor_scale, y + (ry + py) * self.editor_scale
                    p.draw_line(cx - 7, cy, cx + 7, cy, 255, 126, 97)
                    p.draw_line(cx, cy - 7, cx, cy + 7, 255, 126, 97)
        self.draw_editor_preview()

    def handle_event(self, event):
        if event.type in (p.SDL_MOUSEMOTION, p.SDL_MOUSEBUTTONDOWN, p.SDL_MOUSEBUTTONUP):
            self.mouse_position = (event.x, HEIGHT - 1 - event.y)
        if event.type in (p.SDL_TEXTINPUT, p.SDL_TEXTEDITING):
            if self.search_focus:
                if event.type == p.SDL_TEXTEDITING:
                    self.search_composition = event.text
                else:
                    kind = self.search_focus
                    self.search_queries[kind] = (self.search_queries[kind] + event.text)[:64]
                    self.search_offsets[kind] = 0
                    self.search_composition = ""
            return
        if event.type == p.SDL_KEYDOWN and self.search_focus:
            if self.search_composition and event.key in (p.SDLK_RETURN, p.SDLK_KP_ENTER):
                return  # 한글 조합 확정용 Enter는 검색 포커스를 종료하지 않는다.
            if event.key in (p.SDLK_RETURN, p.SDLK_KP_ENTER, p.SDLK_ESCAPE):
                self.focus_search(None)
            elif event.key in (p.SDLK_BACKSPACE, p.SDLK_DELETE) and not self.search_composition:
                kind = self.search_focus
                self.search_queries[kind] = "" if event.key == p.SDLK_DELETE else self.search_queries[kind][:-1]
                self.search_offsets[kind] = 0
            return
        if event.type == p.SDL_MOUSEBUTTONDOWN and self.search_focus:
            x, y = event.x, HEIGHT - 1 - event.y
            if not contains(EVENT_SEARCH, x, y) and not contains(ANIMATION_SEARCH, x, y):
                self.focus_search(None)
        if event.type == p.SDL_KEYDOWN and self.thumbnail_drag:
            if event.key == p.SDLK_ESCAPE:
                self.cancel_drag()
            return
        if event.type == p.SDL_KEYDOWN and self.fps_editing:
            self.handle_fps_key(event.key)
            return
        if event.type == p.SDL_QUIT:
            self.running = False
        elif event.type in (p.SDL_KEYUP, p.SDL_KEYDOWN) and self.screen == "play" and event.key in (p.SDLK_a, p.SDLK_d, p.SDLK_w, p.SDLK_LSHIFT, p.SDLK_RSHIFT):
            key = {p.SDLK_a: "left", p.SDLK_d: "right", p.SDLK_w: "jump", p.SDLK_LSHIFT: "shift", p.SDLK_RSHIFT: "shift"}[event.key]
            if not self.play_paused:
                (self.game.press if event.type == p.SDL_KEYDOWN else self.game.release)(key)
        elif event.type == p.SDL_KEYDOWN and self.screen == "play" and event.key == p.SDLK_SPACE:
            self.toggle_play_pause()
        elif event.type == p.SDL_KEYDOWN and self.screen == "play" and event.key == p.SDLK_r:
            self.reset_play()
        elif event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE:
            if self.drag:
                self.cancel_drag()
            else:
                self.running = False
        elif event.type == p.SDL_KEYDOWN and event.key == p.SDLK_DELETE and self.screen == "editor":
            self.remove_region()
        elif event.type == p.SDL_KEYDOWN and event.key in (p.SDLK_LEFT, p.SDLK_RIGHT):
            if self.screen == "play":
                return
            step = 1 if event.key == p.SDLK_RIGHT else -1
            if self.screen == "editor":
                self.select_frame(step)
            else:
                self.select_animation(self.animation_index + step)
        elif event.type == p.SDL_MOUSEWHEEL:
            mx, my = p.c_int(), p.c_int()
            p.SDL_GetMouseState(p.ctypes.byref(mx), p.ctypes.byref(my))
            self.handle_wheel(event.x, event.y, mx.value, HEIGHT - 1 - my.value)
        elif event.type == p.SDL_MOUSEBUTTONDOWN:
            x, y = event.x, HEIGHT - 1 - event.y
            input_box, apply_box = self.speed_boxes
            if self.fps_editing and not contains(input_box, x, y) and not contains(apply_box, x, y):
                self.cancel_fps_edit()
            if event.button == p.SDL_BUTTON_LEFT:
                index = self.hit_thumbnail(x, y) if self.screen != "play" else None
                if index is not None:
                    self.start_thumbnail_drag(index, x, y)
                    return
                for box, action in self.buttons:
                    if contains(box, x, y):
                        action()
                        return
            self.editor_down(event.button, x, y)
        elif event.type == p.SDL_MOUSEMOTION:
            if self.thumbnail_drag:
                self.update_thumbnail_drag(event.x, HEIGHT - 1 - event.y)
            else:
                self.editor_motion(event.x, HEIGHT - 1 - event.y)
        elif event.type == p.SDL_MOUSEBUTTONUP:
            if self.thumbnail_drag and event.button == p.SDL_BUTTON_LEFT:
                self.finish_thumbnail_drag(event.x, HEIGHT - 1 - event.y)
            else:
                self.editor_up(event.button, event.x, HEIGHT - 1 - event.y)

    def draw(self):
        self.buttons = []
        p.clear_canvas()
        rectangle((0, 0, WIDTH, HEIGHT), BG)
        rectangle(VIEW, PANEL)
        rectangle(THUMBNAILS, PANEL)
        if self.screen == "play":
            self.draw_game_events()
        else:
            self.draw_thumbnails()
        if self.screen == "editor":
            self.draw_editor()
        elif self.screen == "play":
            self.draw_play()
        else:
            with clipped(VIEW):
                p.draw_line(250, 332, 850, 332, 64, 81, 101)
                self.draw_frame(self.frame, WIDTH / 2 + self.view_pan, 332, self.view_scale)
            self.text(40, 628, self.animation.name)
            self.text(40, 600, f"{self.animation.fps:g}fps / 프레임 {self.frame_index + 1}/{len(self.animation.frames)} / 완료 {self.player.completed_cycles}회")
            if self.player.waiting:
                self.text(40, 572, "1초 대기 중", (255, 209, 91))
            elif self.player.finished:
                self.text(40, 572, "재생 완료 · 미리보기를 선택하면 다시 재생", (255, 209, 91))
            if self.frame.rect is None:
                self.text(40, 546, "현재 프레임의 참조 영역이 지정되지 않았습니다.")
        self.text(24, 724, "SONIC")
        self.tab((100, 704, 110, 36), "뷰어", "viewer")
        self.tab((220, 704, 110, 36), "편집", "editor")
        self.tab((340, 704, 110, 36), "Play", "play")
        self.button((470, 704, 130, 36), "JSON 저장", self.save_json)
        self.button((612, 704, 170, 36), "JSON 불러오기", self.load_json)
        self.button((900, 704, 176, 36), "이미지 열기", self.open_image)
        if self.screen == "editor":
            self.draw_editor_controls()
        elif self.screen == "play":
            self.button((24, 663, 200, 30), "재생 [Space]" if self.play_paused else "일시정지 [Space]", self.toggle_play_pause, self.play_paused)
            self.button((236, 663, 200, 30), "다시 시작 [R]", self.reset_play)
            self.draw_speed_control()
        else:
            self.button((24, 663, 245, 30), f"5회 후 대기: {'ON' if self.player.repeat_five else 'OFF'}", self.toggle_five, self.player.repeat_five)
            self.button((280, 663, 220, 30), f"목록 반복: {'ON' if self.player.loop else 'OFF'}", self.toggle_loop, self.player.loop)
            self.draw_speed_control()
        with clipped((24, 20, WIDTH - 48, 34)):
            self.text(24, 32, self.status)
        help_text = ("미리보기 드래그 순서 변경 · 휠 확대/축소 · 중클릭 시트 이동 · 우클릭 피봇 · Delete 영역 제거"
                     if self.screen == "editor" else
                     "미리보기 클릭 선택 · 드래그 순서 변경 · 드래그 중 휠로 목록 넘기기 · Esc 드래그 취소")
        if self.screen == "play":
            help_text = "A/D 이동 → 달리기 · W 점프 · Shift 충전 후 놓아서 스핀 대시 · Space 일시정지 · R 다시 시작"
        self.text(24, 10, help_text, (153, 171, 196))

    def update(self, dt):
        if self.search_focus or self.fps_editing:
            return
        if self.screen == "editor" or self.thumbnail_drag:
            return
        if self.screen == "play":
            if not self.play_paused:
                self.game.update(min(.25, max(0, dt)))
                self.sync_game()
            return
        self.player.update(dt)
        self.animation_index = self.player.index
        self.frame_index = self.player.frame_index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", type=int, default=0, metavar="FRAMES")
    args = parser.parse_args()
    if args.smoke < 0:
        parser.error("--smoke 값은 0 이상이어야 합니다.")
    p.open_canvas(WIDTH, HEIGHT)
    if not p.renderer:
        p.renderer = p.SDL_CreateRenderer(p.window, -1, p.SDL_RENDERER_SOFTWARE)
    if not p.renderer:
        p.close_canvas()
        raise RuntimeError("화면 렌더러를 생성할 수 없습니다.")
    p.hide_lattice()
    p.SDL_SetRenderDrawBlendMode(p.renderer, p.SDL_BLENDMODE_BLEND)
    try:
        app = App()
        previous = time.perf_counter()
        count = 0
        while app.running:
            start = time.perf_counter()
            for event in app_events():
                app.handle_event(event)
            p.SDL_SetWindowTitle(p.window, b"Sonic Animation Viewer")
            app.update(start - previous)
            previous = start
            app.draw()
            p.update_canvas()
            count += 1
            if args.smoke and count >= args.smoke:
                break
            p.delay(max(0, 1 / DISPLAY_FPS - (time.perf_counter() - start)))
    finally:
        p.close_canvas()


if __name__ == "__main__":
    main()
