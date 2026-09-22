from pico2d import *
import os

class Vec2:
    def __init__(self,x,y):
        self.x = x
        self.y = y

class Object:
    def __init__(self, path, x=0, y=0):
        self.pos = Vec2(x,y)
        self.image = load_image(os.getcwd() + path)

# 실행 함수
def run():
    open_canvas()
    # 오브젝트를 만들자
    path = "\\LEC05\\character.png"
    objects = []
    objects.append(Object(path,200,300))
    objects.append(Object(path,400,300))
    objects.append(Object(path,600,300))
    while True:
        handle_events()
        clear_canvas()
        render(objects)
        update_canvas()
        delay(0.016)
    close_canvas()

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
