from pico2d import *

# 아 맨날 x,y 넣는거 귀찮은데
class Vec2:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

# 오브젝트를 일단 선언할까?
class Object:
    def __init__(self):
        self.pos = Vec2()


# 실행 함수
def run():
    open_canvas()
    # 오브젝트를 만들자
    character = Object()
    while True:
        handle_events()
    close_canvas()

# SDL 이벤트 루프
def handle_events():
    events = get_events()
    for event in events:
        if(event.type == SDL_QUIT):
            exit()

if __name__ == "__main__":
    run()
