import os
import math
from pico2d import *
open_canvas(800, 600)

grass = load_image(os.getcwd() + '\\LEC05\\grass.png')
character = load_image(os.getcwd() + '\\LEC05\\character.png')

grass.draw(400, 30)
character.draw(400, 90)


x = 400
y = 300

radius = 50
angle = 0
while True:
    angle += 0.2

    clear_canvas()
    character.draw(x + math.cos(angle) * radius, y + math.sin(angle) * radius)
    update_canvas()

    delay(0.01)

close_canvas()
