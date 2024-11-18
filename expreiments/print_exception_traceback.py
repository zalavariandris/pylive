import sys
import traceback

try:
    result = 1 / 0
except ZeroDivisionError:
    exc_type, exc_value, exc_tb = sys.exc_info()
    print("Exception type:", exc_type)
    print("Exception value:", exc_value)
    print("Traceback:")
    traceback.print_tb(exc_tb)

import traceback

try:
    result = 1 / 0
except Exception as e:
    tb = traceback.TracebackException.from_exception(e)
    print("Formatted Traceback:")
    print(''.join(tb.format()))  # Produces a nicely formatted traceback as a string
