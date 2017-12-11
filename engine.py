"""
Heartbeat:
1. reactive object updates attributes.



# stateful combinators
# stateless combinators (liftable)
# switching upon certain events
# time
# signal function

"""
from core import *

class Ball:
    vx = Reactive()
    x = Reactive()
    vy = Reactive()
    y = Reactive()


add1 = time + 1
square = lambda x: x ** 2

ball = Ball()
ball.vx = 13
ball.x = ball.vx >> Integral()
ball.vy = 5
ball.y = ball.vy >> Integral()

import os
sz = os.get_terminal_size()
term_height = sz.lines
term_width = sz.columns


width, height = 20, 20

char = '.`'

def print_grid(ball):
    x, y = round(now(ball.x)), round(now(ball.y))
    x = max(min(x, width), 0)
    y = max(min(y, height), 0)
    for i in range(height+1):
        if y == i:
            print('{}🧀🐌{}'.format(char*(x-1), char*((width-x))))
        else:
            print(char*(width))
    print('\n' * (term_height - height - 3))


def print_time(x):
    print("it's {}!".format(x))
    return x


def when(cond_behavior, reactor, *args):
    def react():
        if now(cond_behavior):
            reactor(*args)
            return True
        return False
    return react

def reverse_x(obj):
    if now(obj.vx) > 0:
        reactors.append(when(ball.x <= 0, reverse_x, ball))
    else:
        reactors.append(when(abs(ball.x) >= width, reverse_x, ball))
    obj.vx = -1 * now(obj.vx)

def reverse_y(obj):
    if now(obj.vy) > 0:
        reactors.append(when(ball.y <= 0, reverse_y, ball))
    else:
        reactors.append(when(abs(ball.y) >= height, reverse_y, ball))
    obj.vy = -1 * now(obj.vy)

behaviors = [
    lift(ball) >> lift(print_grid)
]

reactors = [
    when(abs(ball.x) >= width, reverse_x, ball),
    when(abs(ball.y) >= height, reverse_y, ball)
]

while True:
    timing.sleep(tick_rate)
    for behavior in behaviors:
        now(behavior)

    for behavior in behaviors:
        behavior.perform_update()

    for behavior in behaviors:
        behavior.make_dirty()

    for reactor in reactors[:]:
        if reactor():
            reactors.remove(reactor)
