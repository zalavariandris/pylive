from textwrap import dedent

from typing import *
import inspect

def evaluate_expressions1():
	print("#", inspect.stack()[0][3])
	chain = {
		1:    "print('hello')",
		'main': "lambda x,y:x+y",
		"res":    "main(5,8)",
		4: "print('inside res:', res)"
	}

	result = None
	global_vars = {}
	local_vars = {}
	for lineno, (name, expr) in enumerate(chain.items()):
		result = eval(expr, global_vars, local_vars)
		if isinstance(name, str):
			local_vars[name] = result
		print(f"{lineno+1:3}. {expr:20.20} {result}")
	

evaluate_expressions1()
