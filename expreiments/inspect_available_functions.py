# from pylive import livescript
# from PySide6.QtGui import *
# from PySide6.QtCore import *
# from PySide6.QtWidgets import *
# import sys
# from types import *

# from inspect import getmembers, isfunction


# def display_list(items):
# 	listview = QListWidget()
# 	for item in items:
# 		listview.addItem(f"{item}")
# 	livescript.display(listview)

# # display a list of available modules
# display_list(sys.modules)

# # display all builin callables
# def get_callables(dictionary:dict):
# 	for key, val in dictionary.items():
# 		IsCallable = callable(val)
# 		IsFunctionType = isinstance(val, FunctionType)
# 		IsFunction = isfunction(val)
# 		if IsCallable:
# 			yield key, val
			
# display_list(get_callables(__builtins__))

# # display module members
# import pathlib
# display_list([name for name, val in getmembers(pathlib) if callable(val)])
