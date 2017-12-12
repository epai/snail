# 🐌 Snail - A Reactive Programming Library for Python

## What is Snail?
Snail provides a simple reactive programming interface  that allows Python programmers to concisely specify the _behavior_ of a reactive application over time.  It takes inspiration from the ideas of Functional Reactive Programming, and augments them to interface with Python objects in a declarative way.

[![Demo Snail](https://j.gifs.com/oQOXn3.gif)](https://github.com/epai/snail/blob/master/game.py)
(Source code in [`game.py`](https://github.com/epai/snail/blob/master/game.py); tested in Python 3.6 on the latest macOS)

## Why Snail?
Open source reactive programming support for Python is sorely lacking.  The only available solution is RxPY, but it uses an observer-based model that has been shown to be less readable than FRP models[^1].  Implementations for FRP-like Python libraries do exist (such as PFRP [^2]), but they remain closed source, and lack useful abstractions in other FRP libraries like Yampa[^3].  Snail is my attempt to bring FRP-like ideas to Python in an open source way, inspired by both PFRP and Yampa.

## Why Reactive Programming?
Reactive applications, such as graphical animations and user-interactive software, are often hard to develop using traditional imperative methods because they involve a mix of data and control flow that can be difficult to reason about.  A reactive programming style simplifies the development of reactive applications by shifting focus to behaviors that change either over time or in response to other behaviors.  Programmers can thus focus on how objects should behave and how data should flow at a high-level, while the reactive library/engine handles all the control flow wiring logic under covers.  

## How Do You Use Snail?
The basic objects in snail are Behaviors, which are streams of values that update over time, and Behavior Functions (BFs), which are functions over Behaviors.  Behaviors and BFs are similar to Yampa Signals and Signal Functions[^3], but are implemented as objects instead of functions.

### Behaviors and BFs
While one could define their own behaviors and BFs, it is often easier to **lift** constants and functions, or compose existing behaviors and BFs.  The below code would print out the number of elapsed seconds after every second:

```
from snail import *

def print_time(s):
	print('{}s have elapsed!')
	
behavior = time >> lift(print_time)

engine = Engine([behavior], tick_rate=1.0)  
engine.run()

# 1s have elapsed!
# 2s have elapsed!
# 3s have elapsed!
…
```

Let’s break down what happened above:

1. All core library features can be imported from the `snail` module.
2. BFs can be applied to Behaviors using `Behavior >> BF` syntax.
3. The behaviors are run using an Engine, which does the dirty-work of making sure data updates properly.  Engine takes in a list of `behaviors`, and optionally a `state` object and `tick_rate` (defaulting to None and 0.01 if neither are provided).

BFs can also be composed using `>>`, and the `lift` function can be omitted if the RHS of `>>` is a behavior of behavior function.  

```
# … import and print_time definition same as above

square = lambda x: x**2
bf = square >> print_time
behavior = time >> bf

# … engine code same

# 1s have elapsed!
# 4s have elapsed!
# 9s have elapsed!
```

The BF will only be made into a Behavior when it is composed with a Behavior.  This works similarly to Yampa’s Arrow Functions[^3], and is a feature that doesn’t exist in PFRP.

### Reactive Entities and Reactors
The features so far are similar to Yampa-style FRP.  Taking inspiration from PFRP[^2], snail also provides Reactive Entities, which are similar to PFRP reactive proxy objects.  Reactive Entities are objects with attributes that are behaviors.

As an example, we can define a simple Ball reactive entity, as shown below:

```
# … import same as above

WIDTH = 20

class Ball(Entity):
    vx = Reactive() (1.)
    x = Reactive()
    
ball = Ball()
ball.vx = 5  # (2.)
ball.x = integral(ball.vx)  # (3.)

def print_ball(ball):
    x = int(now(ball.x))
    rail = '\r{}O{}'.format('-' * x, '-' * (WIDTH - x))
    print(rail, end='') # so it prints on same line
    
behaviors = [
    lift(ball) >> print_ball
]

engine = Engine(behaviors)
engine.run()
```

[![Ball Demo (no bounce)](https://j.gifs.com/2v9Dyz.gif)](https://github.com/epai/snail/blob/master/bounce.py)

Few things to note:

1. Reactive attributes are specified using the `Reactive` attribute descriptor.
2. Constant values (like numbers) are automatically lifted if they’re assigned to a reactive attribute.
3. Since Behaviors can be thought of as continuous functions, we can compute ball’s `x` position by taking the integral of the velocity.

We have a problem, though:  the ball doesn’t bounce back!  We can fix this by adding **reactors**:

```
# … import same as above

WIDTH = 20

class Ball(Entity):
    vx = Reactive() (1.)
    x = Reactive()
    
    def reverse(self):
	    self.vx = -1 * now(self.vx)
    
# … same ball creation code
ball.reactors = [
	reactor(ball.x >= WIDTH, ball.reverse),
	reactor(ball.x < 0, ball.reverse)
]

# … same behavior and engine running code
```

`reactor` allows us to specify **reactor functions** that should execute when certain conditions are met.  These conditions are specified as a Behavior that outputs boolean values (yes, basic operators like `>=` and `<`, as well as `+`, `-`, `/`, etc., all compose), and executes the function when the Behavior outputs `True`.  In this case, the reactor function `reverse` swaps the velocity direction.  Since `ball.x` derives its value from `ball.vx`, when `ball.vx` changes, `ball.x` will also change.

[![Ball Demo (with bounce!)](https://j.gifs.com/MQ9WMO.gif)](https://github.com/epai/snail/blob/master/bounce.py)

## Implementation
Snail uses a simple sampling update strategy like yampa[^2].  While this strategy has drawbacks (computationally intensive to sample on regular intervals and latency is bound by sampling rate[^4]), it’s simple to implement, which helps eliminate bugs such as glitches[^5].  

### Engine
On every sampling tick, the engine performs updates in a few steps:

1. Accesses current values for all behaviors and entities.  This is to ensure any `print` calls run.
2. Each behavior and entity gets updated.
	- Each behavior keeps track of a `dirty` flag that indicates whether it has been updated.  If `dirty` is False, this means the update already happened and shouldn’t be repeated.
	- Updating an Entity involves updating each of the Reactive attributes in that entity, as well as reactors associated with that entity.
	- Since reactors may change Reactive attributes (which other Reactives may depend on), the system uses special `Alias` behaviors, which allows the behaviors to be swapped under an indirection layer.  This prevents attributes from depending on stale behaviors that got overriden.
3. Each behavior and entity gets dirtied (i.e. the `dirty` flag gets set to `False`, so updates can be performed fresh on the next tick).

### Behavior Initiation
Like yampa[^3], snail sidesteps the time-space-leakage problem mentioned in the PFRP paper[^2] by using Behavior Functions and having a specific instantiation process:  Behavior Functions don’t “start” until they’ve been mapped to a specific Behavior.  

### Extensibility
Snail was designed to be extensible.  New Behavior and Behavior Functions can be implemented by subclassing the `Behavior` and `BehaviorFunction` classes respectively.  A caveat is that any new `Behavior` or `BehaviorFunction` classes must be non-blocking (important when defining new forms of IO, like mouse input).  

New `Behavior` classes need only subclass the `curr` and `update` methods, and optionally the `make_dirty` method if it encapsulates another Behavior.  New `BehaviorFunction` classes must specify some `transition` function.  State can be stored as in any other python object through the `__init__` or elsewhere.

## Future Work
Snail is still a work-in-progress, and there are many limitations.  For one, snail currently can only interface with the terminal; porting other frameworks like gui or game frameworks would make snail more practical.  The current example, while, cool, is also minimal.  The hope is to develop some example games, to demonstrate the power of this reactive programming approach.

As mentioned above, snail’s implementation prioritized simplicity over efficiency.  This is okay for simple terminal animations, but will probably not perform well for games with lots of objects and interactions.

(Although snail still worked well when rendering 2000+ balls in the first gif example, with a small amount of lag.)

[![Snail 2000 Balls](https://j.gifs.com/G59KYr.gif)](https://github.com/epai/snail/blob/master/game.py)


## References
[^1]: [An Empirical Study on Program Comprehension with Reactive Programming](http://www.guidosalvaneschi.com/attachments/papers/2014_An-Empirical-Study-on-Program-Comprehension-with-Reactive-Programming_pdf.pdf)

[^2]: [Practical Functional Reactive Programming](http://www.cs.jhu.edu/~roe/padl2014.pdf)

[^3]: [The Yampa Arcade](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.449.2045&rep=rep1&type=pdf)

[^4]: [Wikipedia:  Functional Reactive Programming](https://en.wikipedia.org/wiki/Functional_reactive_programming) 

[^5]: [Wikipedia:  Reactive Programming](https://en.wikipedia.org/wiki/Reactive_programming#Glitches)
