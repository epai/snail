




"""
Heartbeat:
1. reactive object updates attributes.



# stateful combinators
# stateless combinators (liftable)
# switching upon certain events
# time
# signal function

"""


import time as timing

start = timing.time()

import operator

class Behavior:
    def __init__(self):
        self.dirty = True

    def curr(self):
        pass

    def perform_update(self):
        if self.dirty:
            self.update()
        self.dirty = False

    def make_dirty(self):
        self.dirty = True

    def update(self):
        pass

    def compose(self, behavior_func):
        return Mapping(self, behavior_func.transition)

    def __rshift__(self, other):
        if isinstance(other, BehaviorFunction):
            return self.compose(other)
        elif callable(other):
            return self.compose(lift(other))

def add_binop(cls, op, reversible=True):
    def forward(self, other):
        return Function(lambda x: op(x, other)).map_to(self)
    def backward(self, other):
        return op(self, other)

    op_name = '__{}__'.format(op.__name__)
    setattr(cls, op_name, forward)

    if reversible:
        rev_name = '__r{}__'.format(op.__name__)
        setattr(cls, rev_name, backward)

def add_boolop(cls, op, reversible=True):
    def forward(self, other):
        return Function(lambda x: op(x, other)).map_to(self)
    def backward(self, other):
        return op(self, other)

    op_name = '__{}__'.format(op.__name__.strip('_'))
    setattr(cls, op_name, forward)

    if reversible:
        rev_name = '__r{}__'.format(op.__name__.strip('_'))
        setattr(cls, rev_name, backward)

def add_unop(cls, op):
    def forward(self):
        return Function(op).map_to(self)
    op_name = '__{}__'.format(op.__name__)
    setattr(cls, op_name, forward)

add_binop(Behavior, operator.add)
add_binop(Behavior, operator.sub)
add_binop(Behavior, operator.mul)
add_binop(Behavior, operator.truediv)
add_binop(Behavior, operator.floordiv)
add_binop(Behavior, operator.mod)
add_binop(Behavior, operator.pow)
add_binop(Behavior, operator.mod)
add_binop(Behavior, operator.le)
add_binop(Behavior, operator.ge)
add_binop(Behavior, operator.eq)
add_binop(Behavior, operator.ne)
add_binop(Behavior, operator.lt)
add_binop(Behavior, operator.gt)

add_unop(Behavior, operator.abs)

add_boolop(Behavior, operator.and_)
add_boolop(Behavior, operator.or_)

class Mapping(Behavior):
    def __init__(self, behavior, transition):
        super().__init__()
        self.behavior = behavior
        self.transition = transition

    def curr(self):
        return self.transition(self.behavior.curr())

    def update(self):
        self.behavior.perform_update()

class Time(Behavior):
    def __init__(self):
        super().__init__()
        self._start = timing.time()
        self._curr = self._start

    def curr(self):
        return int(self._curr - self._start)

    def update(self):
        self._curr = timing.time()


class Alias(Behavior):
    def __init__(self, behavior):
        super().__init__()
        self.behavior = behavior

    def curr(self):
        return self.behavior.curr()

    def update(self):
        self.behavior.update()

class Constant(Behavior):
    def __init__(self, constant):
        super().__init__()
        self.constant = constant

    def curr(self):
        return self.constant

    # no updating logic

def hold(obj):
    if isinstance(obj, Behavior):
        return Constant(now(obj))
    raise NotImplementedError


class BehaviorFunction:
    def build(self, transition):
        self.transition = transition

    def map_to(self, behavior):
        return Mapping(behavior, self.transition)

    def __rshift__(self, other):
        if isinstance(other, BehaviorFunction):
            return Compose(self, other)
        elif callable(other):
            return Compose(self, lift(other))

class Function(BehaviorFunction):
    def __init__(self, func):
        self.build(func)
lift = Function

class Compose(BehaviorFunction):
    def __init__(self, first, second):
        self.build(lambda val: second.transition(first.transition(val)))

class Integral(BehaviorFunction):
    def __init__(self):
        self.sum = 0

    def transition(self, val):
        self.sum += val * tick_rate
        return self.sum

def now(stream):
    return stream.__class__.curr(stream)

class AutoStorage:
    __counter = 0

    def __init__(self):
        cls = self.__class__
        prefix = cls.__name__
        index = cls.__counter
        self.storage_name = '_{}#{}'.format(prefix, index)
        cls.__counter += 1

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return getattr(instance, self.storage_name, None)

    def __set__(self, instance, value):
        setattr(instance, self.storage_name, value)


class Attribute(AutoStorage):
    def __set__(self, instance, behavior):
        if super().__get__(instance, None) is None:
            alias = Alias(behavior)
            super().__set__(instance, alias)
        else:
            alias = super().__get__(instance, None)
            alias.behavior = behavior

class Reactive(Attribute):
    def __init__(self, default=None):
        super().__init__()

    def __set__(self, instance, value):
        if isinstance(value, BehaviorFunction):
            raise NotImplementedError("reactive attributes must be assigned Behaviors, not BehaviorFunctions")
        elif isinstance(value, Behavior):
            super().__set__(instance, value)
        elif callable(value):
            super().__set__(instance, lift(value))
        else:
            super().__set__(instance, Constant(value))


class EntityMeta(type):
    def __init__(cls, name, bases, attr_dict):
        super().__init__(name, bases, attr_dict)
        for key, attr in attr_dict.items():
            if isinstance(attr, Attribute):
                type_name = type(attr).__name__
                attr.storage_name = '_{}#{}'.format(type_name, key)

class Entity(metaclass=EntityMeta):
    """ Business entity """

class Ball(Entity):
    vx = Reactive()
    x = Reactive()




tick_rate = 0.1
time = Time()
add1 = time + 1
square = lambda x: x ** 2
# print_time = lambda x: print("it's {}!".format(x))

ball = Ball()
ball.vx = 2
ball.x = ball.vx >> Integral()


def pos(x):
    x = int(x)
    print('{}O{}\r'.format('-'*(x), '-'*(10-x)), end='')

def print_time(x):
    print("it's {}!".format(x))
    return x


def when(cond_behavior, reactor, *args):
    def react():
        if now(cond_behavior):
            reactor(*args)
    return react

def reverse_x(obj):
    if now(obj.vx) > 0:
        reactors.append(when(ball.x <= 0, reverse_x, ball))
    else:
        reactors.append(when(abs(ball.x) >= 10, reverse_x, ball))
    obj.vx = -1 * now(obj.vx)

behaviors = [
    ball.x >> lift(pos)
]

reactors = [
    when(abs(ball.x) >= 10, reverse_x, ball)
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

    # try:
    #     listener.join()
    # except MyException as e:
    #     print('{0} was pressed'.format(e.args[0]))
