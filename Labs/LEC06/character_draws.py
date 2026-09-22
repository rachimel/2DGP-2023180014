from pico2d import *
from typing import Self
import os
import math

class Vec2:
    def __init__(self,x,y):
        self.x = x
        self.y = y
    def __add__(self, rhs : Self):
        return Vec2(self.x + rhs.x, self.y + rhs.y)

    def __mul__(self, rhs):
        return Vec2(self.x * rhs, self.y * rhs)

class Object:
    def __init__(self, path, x=0, y=0):
        self.pos = Vec2(x,y)
        self.speed = 0
        self.direction = Vec2(0,0)
        self.image = load_image(os.getcwd() + path)

    def move(self):
        self.pos += self.direction * self.speed
# 실행 함수
def run():
    open_canvas()
    # 오브젝트를 만들자
    path = "\\Labs\\LEC06\\character.png"
    objects = []
    objects.append(Object(path,200,300))
    objects.append(Object(path,400,300))
    objects.append(Object(path,600,300))
    while True:
        handle_events()
        update()
        clear_canvas()
        render(objects)
        update_canvas()
        delay(0.016)
    close_canvas()

# 객체 업데이트 루프
def update(objects):
    pass

# SDL 이벤트 루프
def handle_events():
    events = get_events()
    for event in events:
        if(event.type == SDL_QUIT):
            exit()
        if(event.type == SDL_KEYDOWN):
            pass
# 렌더 함수
def render(objects) :
    for object in objects:
        object.image.draw(object.pos.x, object.pos.y)

if __name__ == "__main__":
    run()
