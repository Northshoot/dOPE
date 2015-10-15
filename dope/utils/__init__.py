__author__ = 'lauril'

from functools import wraps
from blessings import Terminal

def debug(func):
    """
    A simple debugging decorator
    """
    msg = func.__qualname__

    @wraps(func)
    def wrapper(*args, **kwargs):
        t = Terminal()
        print(t.green(msg))
        return func(*args, **kwargs)
    return wrapper


def debugmethods(cls):
    '''
    Apply a decorator to all callable methods of a class
    '''
    for name, val in vars(cls).items():
        if callable(val):
            setattr(cls, name, debug(val))
    return cls
