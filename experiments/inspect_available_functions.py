from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
import sys
from types import *
from inspect import getmembers, isfunction


# display all builin callables
def get_callables(dictionary:list):
	for key, val in dictionary.items():
		IsCallable = callable(val)
		IsFunctionType = isinstance(val, FunctionType)
		IsFunction = isfunction(val)
		if IsCallable:
			yield key, val
			

# display module members
print("## built-ins")
for key in dir(__builtins__):
	if not key.startswith("_"):
		item = getattr(__builtins__,key)
		if callable(item):
			print(f"- {key}")

print("## pathlib")		
import pathlib
import string
for key in dir(pathlib):
	if key[0] in string.ascii_letters: 
		item = getattr(pathlib,key)
		if callable(item):
			print(f"- {key}")
# display_list([name for name, val in getmembers(pathlib) if callable(val)])
