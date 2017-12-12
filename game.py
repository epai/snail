import random
import os

from snail import *


# Reactive entities

class Player(Entity):
    x = Reactive()
    y = Reactive()

    def __init__(self, x=None, y=None, char='[]'):
        super().__init__()
        self.char = char
        self.x = x
        self.y = y

    def down(self):
        self.y = min(now(self.y) + 1, config.height)

    def up(self):
        self.y = max(now(self.y) - 1, 0)

    def right(self):
        self.x = min(now(self.x) + 1, config.width)

    def left(self):
        self.x = max(now(self.x) - 1, 0)


class Ball(Entity):
    vx = Reactive()
    vy = Reactive()
    x = Reactive()
    y = Reactive()

    def __init__(self, char='ZZ'):
        super().__init__()
        self.char = char

    def reverse_x(self):
        self.vx = -1 * now(self.vx)

    def reverse_y(self):
        self.vy = -1 * now(self.vy)


# Some pure behavior helpers

def constrain_x(x):
    return max(min(round(x), config.width), 0)

def constrain_y(y):
    return max(min(round(y), config.height), 0)

def print_grid(state):
    grid = [[char for _ in range(config.width+1)] for _ in range(config.height+1)]
    for ball in state.balls:
        x, y = constrain_x(now(ball.x)), constrain_y(now(ball.y))
        grid[y][x] = ball.char
    x, y = constrain_x(now(state.player.x)), constrain_y(now(state.player.y))
    grid[y][x] = player.char
    for row in grid:
        print(''.join(row))
    print('\n' * (term_height - config.height - 3))

def quit(done):
    if done:
        raise KeyboardInterrupt


# Setup code

sz = os.get_terminal_size()
term_height = sz.lines
term_width = sz.columns
char = '.`'

class Config:
    width = 40
    height = 30

class State:
    player = None
    balls = []

state = State()
config = Config()

behaviors = [
    keyboard,
    lift(state) >> lift(print_grid),
    (keyboard == 'esc') >> quit
]



player = Player(x=config.width // 2, y=config.height // 2, char='🧀🐌')
player.reactors = [
    reactor(keyboard == 'down', player.down),
    reactor(keyboard == 'up', player.up),
    reactor(keyboard == 'left', player.left),
    reactor(keyboard == 'right', player.right)
]
state.player = player

for _ in range(2000):
    ball = Ball()
    ball.vx = random.randint(5, 15)
    ball.x = integral(ball.vx) + random.randint(0, config.width)
    ball.vy = random.randint(5, 15)
    ball.y = integral(ball.vy) + random.randint(0, config.height)

    ball.reactors = [
        reactor(ball.x >= config.width, ball.reverse_x),
        reactor(ball.x < 0, ball.reverse_x),
        reactor(ball.y >= config.height, ball.reverse_y),
        reactor(ball.y < 0, ball.reverse_y),
    ]

    state.balls.append(ball)


# Main reactive loop

engine = Engine(behaviors, state=state, tick_rate=0.03)  # roughly 30fps
try:
    engine.run()
except KeyboardInterrupt:
    print('done')

