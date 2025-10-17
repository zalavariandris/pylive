import ast

def get_parent_node(script: str, line_number: int):
    """
    Get the parent AST node for a specific line in a Python script.

    :param script: The Python script as a string.
    :param line_number: The line number (1-based) for which the parent node is needed.
    :return: The parent node of the given line, or None if not found.
    """
    class ParentNodeVisitor(ast.NodeVisitor):
        def __init__(self, line_number):
            self.line_number = line_number
            self.parent_node = None
            self.current_parent = None  # Keeps track of the current parent during traversal
        
        def visit(self, node):
            if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                if node.lineno <= self.line_number <= node.end_lineno:
                    # Found the enclosing node; save its parent
                    self.parent_node = self.current_parent
            
            # Temporarily set the current node as the parent and visit children
            previous_parent = self.current_parent
            self.current_parent = node
            super().visit(node)
            self.current_parent = previous_parent  # Restore the previous parent after visiting
        
    # Parse the script into an AST
    tree = ast.parse(script)
    
    # Visit the tree to find the parent node
    visitor = ParentNodeVisitor(line_number)
    visitor.visit(tree)
    
    return visitor.parent_node

# Example Usage
script = """\
def example_function():
    if True:
        print("Hello, World!")
    else:
        print("Goodbye, World!")

for i in range(3):
    print(i)
"""

line_number = 3  # Inside the 'if' block
parent_node = get_parent_node(script, line_number)
print(ast.dump(parent_node, indent=4))
