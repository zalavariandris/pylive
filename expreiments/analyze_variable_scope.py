import ast

class VariableScopeAnalyzer(ast.NodeVisitor):
	def __init__(self):
		# Stack to keep track of variable scopes
		self.scopes = [{}]  # Each scope is a dictionary {variable_name: ast.Name node}

	def visit_FunctionDef(self, node):
		# Create a new scope for the function
		self.scopes.append({})
		# Visit function body
		self.generic_visit(node)
		# Pop the function scope when done
		self.scopes.pop()

	def visit_ClassDef(self, node):
		# Create a new scope for the class
		self.scopes.append({})
		# Visit class body
		self.generic_visit(node)
		# Pop the class scope when done
		self.scopes.pop()

	def visit_ListComp(self, node):
		# Create a new scope for the list comprehension
		self.scopes.append({})
		# Visit the generators and the body of the comprehension
		self.generic_visit(node)
		# Pop the list comprehension scope when done
		self.scopes.pop()

	def visit_Name(self, node):
		print(node.id)
		if isinstance(node.ctx, ast.Store):
			# Assignments go to the current scope
			self.scopes[-1][node.id] = node
		elif isinstance(node.ctx, ast.Load):
			# Usages are checked against available scopes (starting from innermost)
			for scope in reversed(self.scopes):
				if node.id in scope:
					# This variable is found in the current or parent scope
					print(f"Variable '{node.id}' at line {node.lineno} "
						  f"refers to the same as defined at line {scope[node.id].lineno}")
					break
			else:
				# If not found, it's unbound
				print(f"Variable '{node.id}' at line {node.lineno} is unbound")
		# Continue traversing
		self.generic_visit(node)


# Test Example
code = """[item for item in range(5)]"""

# Parse the code
tree = ast.parse(code)

# Analyze the variable scopes
analyzer = VariableScopeAnalyzer()
analyzer.visit(tree)
