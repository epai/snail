import random
import os

from snail import *

class Config:
    width = 30
    height = 24

class State:
    player = None
    balls = []

    @property
    def entities(self):
        objects = []
        objects.append(self.player)
        objects.extend(self.balls)
        return objects

state = State()
config = Config()

class Entity:
    def __init__(self):
        self.reactors = []

    def perform_update(self, state):
        for reactor in self.reactors:
            reactor.perform_update(state)

    def make_dirty(self):
        for reactor in self.reactors:
            reactor.make_dirty()


class Player(Entity):
    x = Reactive()
    y = Reactive()

    def __init__(self, x=None, y=None, char='[]'):
        super().__init__()
        self.char = char
        self.x = x
        self.y = y

    @reactor
    def down(self):
        self.y = min(now(self.y) + 1, config.height)

    @reactor
    def up(self):
        self.y = max(now(self.y) - 1, 0)

    @reactor
    def right(self):
        self.x = min(now(self.x) + 1, config.width)

    @reactor
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

    @reactor
    def reverse_x(self):
        self.vx = -1 * now(self.vx)

    @reactor
    def reverse_y(self):
        self.vy = -1 * now(self.vy)


sz = os.get_terminal_size()
term_height = sz.lines
term_width = sz.columns

char = '.`'

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


# Setup code

behaviors = [
    time,
    lift(state) >> lift(print_grid),
    keyboard,
]

player = Player(x=0, y=0, char='🧀🐌')
player.reactors = [
    (keyboard == 'down') >> player.down,
    (keyboard == 'up') >> player.up,
    (keyboard == 'left') >> player.left,
    (keyboard == 'right') >> player.right,
]
state.player = player

for _ in range(10):
    ball = Ball()
    ball.vx = random.randint(5, 15)
    ball.x = (ball.vx >> Integral()) + random.randint(0, config.width)
    ball.vy = random.randint(5, 15)
    ball.y = (ball.vy >> Integral()) + random.randint(0, config.height)

    ball.reactors = [
        (ball.x >= config.width) >> ball.reverse_x,
        (ball.x < 0) >> ball.reverse_x,
        (ball.y >= config.height) >> ball.reverse_y,
        (ball.y < 0) >> ball.reverse_y
    ]

    state.balls.append(ball)


# Main reactive loop

while True:
    timing.sleep(tick_rate)

    for behavior in behaviors:
        now(behavior)

    for behavior in behaviors:
        behavior.perform_update(state)

    for entity in state.entities:
        for reactor in entity.reactors:
            now(reactor)
        entity.perform_update(state)

    for entity in state.entities:
        entity.make_dirty()

    for behavior in behaviors:
        behavior.make_dirty()

