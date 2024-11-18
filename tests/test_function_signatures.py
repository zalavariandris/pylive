import inspect
from typing import *
def sample_function(a: int, b: str, c: float = 5.0, props:List=[]) -> bool:
	return True



def format_type(annotation):
	"""Helper function to format type annotations as readable strings."""
	if hasattr(annotation, '__name__'):  # For built-in types like int, float
		return annotation.__name__
	elif hasattr(annotation, '__origin__'):  # For generic types like List, Dict
		origin = annotation.__origin__
		args = ", ".join(format_type(arg) for arg in annotation.__args__) if annotation.__args__ else ""
		return f"{origin.__name__}[{args}]" if args else origin.__name__
	else:
		return str(annotation)  # Fallback for unusual cases

def format_param(param)->str:
	text = ""
	if param.kind == inspect.Parameter.VAR_POSITIONAL:
		text += "*"
	if param.kind == inspect.Parameter.VAR_KEYWORD:
		text += "**"
	text += f"{param.name}"
	
	# Add type annotation if available
	if param.annotation is not inspect.Parameter.empty:
		text += f":{format_type(param.annotation)}"
	
	# Add default value if available
	if param.default is not inspect.Parameter.empty:
		text += f"={repr(param.default)}"
	
	return text

def format_signature(fn):
	# Get the signature of the function
	sig = inspect.signature(fn)

	# Build the formatted signature text
	text = f"{fn.__name__}"
	text+="("
	text+=", ".join( [format_param(param) for param in sig.parameters.values()] )
	text+=")"
	
	# Output the return type annotation if present
	if sig.return_annotation is not inspect.Signature.empty:
		text += f"-> {format_type(sig.return_annotation)}"
	
	return text
	

import unittest
class TestBuiltIns(unittest.TestCase):
	def test_print_function(self):
		pass

class TestSimplefunctions(unittest.TestCase):
	...