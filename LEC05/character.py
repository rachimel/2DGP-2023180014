import os
from pico2d import *

open_canvas(800, 600)

grass = load_image(os.getcwd() + '\\LEC05\\grass.png')
character = load_image(os.getcwd() + '\\LEC05\\character.png')

grass.draw(400, 30)
character.draw(400, 90)


x = 400
y = 300
dir = 'RIGHT'

moveTime = 0
while True:
    moveTime += 2
    if(dir == 'RIGHT'):
        x += 2
    elif(dir == 'UP'):
        y += 2
    elif(dir == 'LEFT'):
        x -= 2
    elif(dir == 'DOWN'):
        y -= 2

    if(moveTime > 80):
        if(dir == 'RIGHT'):
            dir = 'UP'
        elif (dir == 'UP'):
            dir = 'LEFT'
        elif (dir == 'LEFT'):
            dir = 'DOWN'
        elif (dir == 'DOWN'):
            dir = 'RIGHT'
        moveTime = 0

    clear_canvas()
    character.draw(x, y)
    update_canvas()

    delay(0.01)

close_canvas()
