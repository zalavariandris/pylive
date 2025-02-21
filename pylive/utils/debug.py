import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

import inspect
# def log_caller():
#     if frame:=inspect.currentframe():
#         logger.debug(frame.f_code.co_name)

def log_caller():
    stack = inspect.stack()

    # stack[1] gives previous function ('info' in our case)
    # stack[2] gives before previous function and so on

    fn = stack[2][1]
    ln = stack[2][2]
    func = stack[2][3]

    logger.debug(f"caller: {fn}, {ln}, {func}")
    # return fn, func, ln

def logSignal(self):
    ...

import functools
def log_function_call(func):
    """
    A decorator that logs the function name and its arguments when the function is called.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        args_repr = ", ".join(repr(a) for a in args)
        kwargs_repr = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
        signature = ", ".join(filter(None, [args_repr, kwargs_repr]))
        print(f"Calling {func.__name__}({signature})")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned {result!r}")
        return result
    return wrapper