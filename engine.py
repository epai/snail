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
from input import Keyboard

class State:
    balls = []

state = State()

class Ball:
    vx = Reactive()
    x = Reactive()
    vy = Reactive()
    y = Reactive()

    def __init__(self, char='ZZ'):
        self.char = char
        state.balls.append(self)


add1 = time + 1
square = lambda x: x ** 2

ball = Ball(char='🧀🐌')
ball.vx = 0
ball.x = 0
ball.vy = 0
ball.y = 0

import random

import os
sz = os.get_terminal_size()
term_height = sz.lines
term_width = sz.columns


width, height = 30, 24

char = '.`'

def print_grid(state):
    grid = [[char for _ in range(width+1)] for _ in range(height+1)]
    for ball in state.balls:
        x, y = round(now(ball.x)), round(now(ball.y))
        x = max(min(x, width), 0)
        y = max(min(y, height), 0)
        grid[y][x] = ball.char
    for row in grid:
        print(''.join(row))
    print('\n' * (term_height - height - 3))


def print_time(x):
    print("it's {}!".format(x))
    return x


def when(cond_behavior, reactor, *args, recurring=True):
    def react():
        if now(cond_behavior):
            reactor(*args)
            return True
        return False
    react.recurring = recurring
    return react

def reverse_x(obj):
    if now(obj.vx) > 0:
        reactors.append(when(obj.x <= 0, reverse_x, obj, recurring=False))
    else:
        reactors.append(when(abs(obj.x) >= width, reverse_x, obj, recurring=False))
    obj.vx = -1 * now(obj.vx)

def reverse_y(obj):
    if now(obj.vy) > 0:
        reactors.append(when(obj.y <= 0, reverse_y, obj, recurring=False))
    else:
        reactors.append(when(abs(obj.y) >= height, reverse_y, obj, recurring=False))
    obj.vy = -1 * now(obj.vy)

def change(key):
    global char
    if key:
        char = key*2

def up(ball):
    ball.y = max(now(ball.y) - 1, 0)

def down(ball):
    ball.y = min(now(ball.y) + 1, height)

def left(ball):
    ball.x = max(now(ball.x) - 1, 0)

def right(ball):
    ball.x = min(now(ball.x) + 1, width)


keyboard = Keyboard()

behaviors = [
    lift(state) >> lift(print_grid),
    keyboard,
]

reactors = [
    when(keyboard == 'up', up, ball),
    when(keyboard == 'down', down, ball),
    when(keyboard == 'left', left, ball),
    when(keyboard == 'right', right, ball),
    # when(keyboard == 'up', announce, keyboard),
]

for _ in range(50):
    ball_x = Ball()
    ball_x.vx = random.randint(5, 15)
    ball_x.x = (ball_x.vx >> Integral()) + random.randint(0, width)
    ball_x.vy = random.randint(5, 15)
    ball_x.y = (ball_x.vy >> Integral()) + random.randint(0, height)
    behaviors.append(ball_x.vy)
    behaviors.append(ball_x.vx)
    reactors.append(when(abs(ball_x.x) >= width, reverse_x, ball_x, recurring=False))
    reactors.append(when(abs(ball_x.y) >= height, reverse_y, ball_x, recurring=False))

while True:
    timing.sleep(tick_rate)
    for behavior in behaviors:
        now(behavior)

    for behavior in behaviors:
        behavior.perform_update()

    for behavior in behaviors:
        behavior.make_dirty()

    for reactor in reactors[:]:
        if reactor() and not reactor.recurring:
            reactors.remove(reactor)
