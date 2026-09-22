from pico2d import *

# 오브젝트를 일단 선언할까?
class Object:
    def __init__(self):
        self.x = 0;
        self.y = 0;

# 실행 함수
def run():
    open_canvas()
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
