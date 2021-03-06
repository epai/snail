import termios
import sys
import fcntl
import os

from snail.core import Behavior
from snail.utils import nostdout

class Keyboard(Behavior):
    def __init__(self):
        super().__init__()
        self.key = None

    def curr(self):
        return self.key

    def update(self, state):
        key = get_key_stroke()
        self.key = key



# credits:  https://stackoverflow.com/a/46540095

def get_key_code(blocking = True):
    with nostdout():
        fd = sys.stdin.fileno()
        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)
        if not blocking:
            oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NDELAY | os.O_NONBLOCK |os.O_SYNC)
        try:
            return ord(sys.stdin.read(1))
        except IOError:
            return 0
        except TypeError:
            return 0
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
            if not blocking:
                fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)

def get_key_stroke():
    code  = get_key_code(blocking=False)
    if code == 27:
        code2 = get_key_code(blocking = False)
        if code2 == 0:
            return "esc"
        elif code2 == 91:
            code3 = get_key_code(blocking = False)
            if code3 == 65:
                return "up"
            elif code3 == 66:
                return "down"
            elif code3 == 68:
                return "left"
            elif code3 == 67:
                return "right"
            else:
                return "esc?"
    elif code == 127:
        return "backspace"
    elif code == 9:
        return "tab"
    elif code == 10:
        return "return"
    elif code == 195 or code == 194:
        code2 = get_key_code(blocking = False)
        return chr(code)+chr(code2) # utf-8 char
    elif code > 0:
        return chr(code)

if __name__ == '__main__':
    import time
    while True:
        time.sleep(0.1)
        key = getKeyStroke()


