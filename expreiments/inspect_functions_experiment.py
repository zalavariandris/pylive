import inspect
from typing import *
def sample_function(a: int, b: str, c: float = 5.0, props:List=[]) -> bool:
    return True

# Get the signature of the function
sig = inspect.signature(sample_function)

# Print argument details
print("Arguments:")
for param in sig.parameters.values():
    print(f"- Name: {param.name}, Default: {param.default}, Annotation: {param.annotation}")

# Output the return type
print(f"Return type: {sig.return_annotation}")
