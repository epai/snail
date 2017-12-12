from snail import *

class Ball(Entity):
    vx = Reactive()
    x = Reactive()

    def reverse(self):
        self.vx = -1 * now(self.vx)

WIDTH = 20

ball = Ball()
ball.vx = 5
ball.x = integral(ball.vx)

ball.reactors = [
    reactor(ball.x >= WIDTH, ball.reverse),
    reactor(ball.x < 0, ball.reverse),
]

def print_ball(ball):
    x = int(now(ball.x))
    rail = '\r{}O{}'.format('-' * x, '-' * (WIDTH - x))
    print(rail, end='') # so it prints on same line

behaviors = [
    lift(ball) >> print_ball
]

engine = Engine(behaviors)
engine.run()
