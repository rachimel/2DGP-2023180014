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
    def __init__(self, path, x=0, y=0, move_type=""):
        self.pos = Vec2(x,y)
        self.speed = 0
        self.angular_speed = 5
        self.angle = 0
        self.direction = Vec2(0,0)
        self.image = load_image(os.getcwd() + path)
        self.move_type = move_type

    def update(self):
        self.angle += self.angular_speed
        if self.move_type == "Circle":
            self.direction = Vec2(math.cos(math.radians(self.angle)), math.sin(math.radians(self.angle)))
        elif self.move_type == "Square" and self.angle % 90 == 0:
            self.direction = Vec2(-self.direction.y, self.direction.x)
        elif self.move_type == "Triangle" and self.angle % 60 == 0:
            x = self.direction.x
            y = self.direction.y
            self.direction = Vec2(x * math.cos(math.radians(120)) - y * math.sin(math.radians(120)),
                x * math.sin(math.radians(120)) + y * math.cos(math.radians(120)))

    def move(self):
        self.pos += self.direction * self.speed


# 실행 함수
def run():
    open_canvas()
    # 오브젝트를 만들자
    path = "\\Labs\\LEC06\\character.png"
    objects = []
    objects.append(Object(path,200,300, "Circle"))
    objects[0].speed = 5
    objects.append(Object(path,400,300, "Square"))
    objects[1].direction = Vec2(1, 0)
    objects[1].speed = 5
    objects.append(Object(path,600,300, "Triangle"))
    objects[2].direction = Vec2(1, 0)
    objects[2].speed = 5

    while True:
        handle_events(objects)
        update(objects)
        clear_canvas()
        render(objects)
        update_canvas()
        delay(0.016)
    close_canvas()

# 객체 업데이트 루프
def update(objects):
    for object in objects:
        object.update()
        object.move()

# SDL 이벤트 루프
def handle_events(objects):
    events = get_events()
    for event in events:
        if(event.type == SDL_QUIT):
            exit()
        elif(event.type == SDL_KEYDOWN):
            handle_key_events(event, objects)

def handle_key_events(event, objects):
    if(event.key == SDLK_EQUALS):
        for object in objects:
            object.speed += 1
    elif(event.key == SDLK_MINUS):
        for object in objects:
            object.speed -= 1

# 렌더 함수
def render(objects) :
    for object in objects:
        object.image.draw(object.pos.x, object.pos.y)

if __name__ == "__main__":
    run()
