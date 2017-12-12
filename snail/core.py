import time as timing
import operator

tick_rate = 0.01

def now(stream):
    return stream.__class__.curr(stream)

def lift(obj):
    if callable(obj):
        return Function(obj)
    elif isinstance(obj, Behavior) or isinstance(obj, BehaviorFunction):
        return obj
    else:
        return Constant(obj)

def hold(obj):
    if isinstance(obj, Behavior):
        return Constant(now(obj))
    raise NotImplementedError

# Decorator form:

# def reactor(func):
#     def decorated(self, cond, *args):
#         if cond:
#             func(self, *args)
#     return decorated

# function form:

def reactor(cond, func):
    def decorated(cond, *args):
        if cond:
            func(*args)
    return cond >> decorated

class Behavior:
    def __init__(self):
        self.dirty = True

    def curr(self):
        pass

    def update(self, state):
        pass

    def perform_update(self, state):
        if self.dirty:
            self.update(state)
        self.dirty = False

    def make_dirty(self):
        self.dirty = True

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

    def update(self, state):
        self.behavior.perform_update(state)

    def make_dirty(self):
        super().make_dirty()
        self.behavior.make_dirty()

class Time(Behavior):
    def __init__(self):
        super().__init__()
        self._start = timing.time()
        self._curr = self._start

    def curr(self):
        return int(self._curr - self._start)

    def update(self, state):
        self._curr = timing.time()

class Alias(Behavior):
    def __init__(self, behavior):
        super().__init__()
        self.behavior = behavior

    def curr(self):
        return self.behavior.curr()

    def update(self, state):
        self.behavior.perform_update(state)

    def make_dirty(self):
        super().make_dirty()
        self.behavior.make_dirty()

class Constant(Behavior):
    def __init__(self, constant):
        super().__init__()
        self.constant = constant

    def curr(self):
        return self.constant



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

class Compose(BehaviorFunction):
    def __init__(self, first, second):
        self.build(lambda val: second.transition(first.transition(val)))

class Integral(BehaviorFunction):
    def __init__(self):
        self.sum = 0

    def transition(self, val):
        self.sum += val * tick_rate
        return self.sum



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
            return getattr(instance, self.storage_name)

    def __set__(self, instance, value):
        setattr(instance, self.storage_name, value)

class Reactive(AutoStorage):
    def set_behavior(self, instance, behavior):
        if getattr(instance, self.storage_name, None):
            # we have a behavior!
            alias = getattr(instance, self.storage_name)
            alias.behavior = behavior
        else:
            # we need to create a new alias
            alias = Alias(behavior)
            super().__set__(instance, alias)

    def __set__(self, instance, value):
        if isinstance(value, BehaviorFunction):
            raise NotImplementedError("reactive attributes must be assigned Behaviors, not BehaviorFunctions")
        elif isinstance(value, Behavior):
            self.set_behavior(instance, value)
        elif callable(value):
            self.set_behavior(instance, lift(value))
        else:
            self.set_behavior(instance, Constant(value))

entities = []

class Entity:
    def __init__(self):
        self.reactors = []
        entities.append(self)

    def perform_update(self, state):
        for reactor in self.reactors:
            reactor.perform_update(state)

    def make_dirty(self):
        for reactor in self.reactors:
            reactor.make_dirty()

class Engine:
    def __init__(self, behaviors, entities=entities, state=None, tick_rate=tick_rate):
        self.state = state
        self.entities = entities
        self.behaviors = behaviors
        self.tick_rate = tick_rate

    def run(self):
        global tick_rate
        tick_rate = self.tick_rate

        while True:
            timing.sleep(self.tick_rate)

            for behavior in self.behaviors:
                now(behavior)

            for behavior in self.behaviors:
                behavior.perform_update(self.state)

            for entity in self.entities:
                for reactor in entity.reactors:
                    now(reactor)
                entity.perform_update(self.state)

            for entity in self.entities:
                entity.make_dirty()

            for behavior in self.behaviors:
                behavior.make_dirty()

# class Attribute(AutoStorage):
#     def __set__(self, instance, behavior):
#         if super().__get__(instance, None) is None:
#             alias = Alias(behavior)
#             super().__set__(instance, alias)
#         else:
#             alias = super().__get__(instance, None)
#             alias.behavior = behavior



# class EntityMeta(type):
#     def __init__(cls, name, bases, attr_dict):
#         super().__init__(name, bases, attr_dict)
#         for key, attr in attr_dict.items():
#             if isinstance(attr, Attribute):
#                 type_name = type(attr).__name__
#                 attr.storage_name = '_{}#{}'.format(type_name, key)

# class Entity(metaclass=EntityMeta):
#     """ Business entity """

