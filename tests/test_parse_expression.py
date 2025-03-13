import ast

class UnboundedNameFinder(ast.NodeVisitor):
    def __init__(self):
        self.unbounded_names = set()
        self.defined_names = set()
        self.comprehension_names = set()  # Tracks variables bound in comprehensions

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):  # Variable is being used
            if node.id not in self.defined_names and node.id not in self.comprehension_names:
                self.unbounded_names.add(node.id)
        elif isinstance(node.ctx, ast.Store):  # Variable is being assigned
            self.defined_names.add(node.id)
        self.generic_visit(node)

    def visit_Assign(self, node):
        # Process assigned variables before visiting right-hand side
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.defined_names.add(target.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Function names should be considered defined
        self.defined_names.add(node.name)
        self.generic_visit(node)

    def visit_ListComp(self, node):
        # Handle comprehensions correctly
        for generator in node.generators:
            if isinstance(generator.target, ast.Name):
                self.comprehension_names.add(generator.target.id)
            elif isinstance(generator.target, (ast.Tuple, ast.List)):  # Handles tuple unpacking
                for elt in generator.target.elts:
                    if isinstance(elt, ast.Name):
                        self.comprehension_names.add(elt.id)
        self.generic_visit(node)

    def visit_DictComp(self, node):
        for generator in node.generators:
            if isinstance(generator.target, ast.Name):
                self.comprehension_names.add(generator.target.id)
        self.generic_visit(node)

    def visit_SetComp(self, node):
        for generator in node.generators:
            if isinstance(generator.target, ast.Name):
                self.comprehension_names.add(generator.target.id)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node):
        for generator in node.generators:
            if isinstance(generator.target, ast.Name):
                self.comprehension_names.add(generator.target.id)
        self.generic_visit(node)

def find_unbounded_names(expr):
    tree = ast.parse(expr, mode='eval')
    finder = UnboundedNameFinder()
    finder.visit(tree)
    return finder.unbounded_names

import unittest

class TestExpressions(unittest.TestCase):
    def test_expressions(self):
        expr = "y + z"
        self.assertEqual( find_unbounded_names(expr),  set(['y', 'z']) )

    def test_list_comprehension(self):
        expr = '[item for item in items]'
        self.assertEqual( find_unbounded_names(expr),  set(['items']) )

    def test_generator_comprehension(self):
        expr = '(num for num in numbers)'
        self.assertEqual( find_unbounded_names(expr),  set(['numbers']) )

    def test_tuple_unpacking(self):
        expr = '[(key, value) for key, value in data.items()]'
        self.assertEqual( find_unbounded_names(expr),  set(['data']) )

    def test_dict_comprehension(self):
        expr = '{key: value for key, value in data.items()}'
        self.assertEqual( find_unbounded_names(expr),  set(['data']) )

if __name__ == "__main__":
    unittest.main()
