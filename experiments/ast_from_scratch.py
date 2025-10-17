#%% setup
from PySide6.QtWidgets import *
from pylive.QtLiveApp import display
import ast

#%% update
# Create the Module containing the AST

import ast
import ast

# Construct the AST nodes manually with 'lineno' and 'col_offset'
import ast

# Construct the AST nodes manually
import_node = ast.ImportFrom(
    module='pathlib',
    names=[ast.alias(name='Path', asname=None)],
    level=0
)

assignment1 = ast.Assign(
    targets=[ast.Name(id='cwd1', ctx=ast.Store(), lineno=2, col_offset=0)],
    value=ast.Call(
        func=ast.Attribute(
            value=ast.Name(id='Path', ctx=ast.Load(), lineno=2, col_offset=8),
            attr='cwd',
            ctx=ast.Load(),
            lineno=2,
            col_offset=8
        ),
        args=[],
        keywords=[],
        lineno=2,
        col_offset=8
    ),
    lineno=2,
    col_offset=0
)

assignment2 = ast.Assign(
    targets=[ast.Name(id='print1', ctx=ast.Store(), lineno=2, col_offset=0)],
	value = ast.Call(
	        func=ast.Name(id='print', ctx=ast.Load(), lineno=3, col_offset=0),
	        args=[
	            ast.Name(id='cwd1', ctx=ast.Load(), lineno=3, col_offset=6)
	        ],
	        keywords=[],
	        lineno=3,
	        col_offset=0
	    ),
	lineno=3,
	col_offset=0
)

# Create the Module containing the AST
module = ast.Module(
    body=[import_node, assignment1, assignment2],
    type_ignores=[]
)

# Convert the AST back to source code to verify
generated_code = ast.unparse(module)
display(f"'{generated_code}'")
