import sys
import traceback


"""
Capture and print Exceptions
"""
SCRIPT = """\
print("ok")
print("running"):
result = 1 / 0
"""

try:
    exec(SCRIPT)  # This will raise a ZeroDivisionError
except SyntaxError as e:
	print("SyntaxError:", e.lineno)
except Exception as e:
    print(f"{e}:")
    tb = traceback.TracebackException.from_exception(e)
    
    # Loop through the stack to print the filename, line number, function name, and code
    for frame in tb.stack:
        print(f"  File: {frame.filename}, Line: {frame.lineno}, Function: {frame.name}, Code: {frame.line}")

    # Alternatively, get just the line number from the last frame (where the exception was raised)
    last_frame = tb.stack[-1]  # The last frame is where the exception occurred
    print(f"  Line number of the exception: {last_frame.lineno}")
