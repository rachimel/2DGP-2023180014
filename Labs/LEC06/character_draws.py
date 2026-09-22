from pico2d import *
import os

# 아 맨날 x,y 넣는거 귀찮은데
class Vec2:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

# 오브젝트를 일단 선언할까?
class Object:
    def __init__(self, path):
        self.pos = Vec2()
        # 일단 귀찮으니까 이미지를 때려박자
        self.image = load_image(os.getcwd() + path)
# 실행 함수
def run():
    open_canvas()
    # 오브젝트를 만들자

    while True:
        handle_events()
    close_canvas()

# SDL 이벤트 루프
def handle_events():
    events = get_events()
    for event in events:
        if(event.type == SDL_QUIT):
            exit()
        # 키보드 입력을 넣으면 더 재밌겠지?
        if(event.type == SDL_KEYDOWN):
            pass

# 일단 오브젝트를 그려야겠지...
def render(objects) : # (objects) <- 이게 복사가 아니라고!?!?
    for object in objects:
        object.image.draw()

if __name__ == "__main__":
    run()
