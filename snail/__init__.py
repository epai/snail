from snail.core import *
from snail.input import Keyboard

start = timing.time()
time = Time()

keyboard = Keyboard()

def integral(behavior):
    return behavior >> Integral()