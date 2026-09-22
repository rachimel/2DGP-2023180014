from pico2d import *

def handle_events():
    events = get_events()
    for event in events:
        if(event.type == SDL_QUIT):
            exit()

open_canvas()
while True:
    handle_events()
close_canvas()
