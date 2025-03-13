
###
### TODO
### - test if modules can be loaded from the folder of the current pylive graph file
### - test single and multi input ports
###   non-multi inlets, when connected, should disconnect previous links
### - test missing packages
### - test create a print node, than change its expression to all node.
###


from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtTest import QSignalSpy

import unittest

from pylive.VisualCode_v6.py_graph_model import PyGraphModel
from textwrap import dedent

import sys
app = QApplication( sys.argv )

class TestImportModel(unittest.TestCase):
    def test_load_module(self):
        ...

    def test_unload_module(self):
        ...

class TestCRUD(unittest.TestCase):
    def test_update_expression(self):
        model = PyGraphModel()
        model.addNode("n1", expression="print")
        model.setData("n1", 'expression', "all")


class TestValues(unittest.TestCase):
    def test_string_value(self):
        model = PyGraphModel()
        model.addNode(name="name", expression="'Mása'", kind='value')
        self.assertEqual(model.data("name", 'result'), (None, "Mása"))

    def test_int_value(self):
        model = PyGraphModel()
        model.addNode(name="name", expression="5", kind='value')
        self.assertEqual(model.data("name", 'result'), (None, 5))

    def test_path_value(self):
        from pathlib import Path
        model = PyGraphModel()
        model.setImports(['pathlib'])
        model.addNode(name="name", expression="pathlib.Path.cwd()", kind='value')
        self.assertEqual(model.data("name", 'result'), (None, Path.cwd()))


class TestOperators(unittest.TestCase):
    def test_standard_lib_operators(self):
        model = PyGraphModel()
        model.setImports(["operator"])
        model.addNode("two", "2", kind='value')
        model.addNode("three", "3", kind='value')

        model.addNode("mult", "operator.mul", kind='operator')
        model.linkNodes("two", "mult", "out", "a")
        model.linkNodes("three", "mult", "out", "b")

        self.assertEqual(model.data("mult", 'result'), (None, 6))

    @unittest.skip("not implemented yet")
    def test_builtin_operator(self):
        model = PyGraphModel()
        model.addNode("map1", "map", kind='operator')
        self.assertEqual(model.data("map1", 'result'), (None, None))


class TestExpressions(unittest.TestCase):
    def test_simple_value_expression(self):
        model = PyGraphModel()
        model.addNode("two", "2", kind='expression')
        self.assertEqual(model.data("two", 'result'), (None, 2))

    def test_expression_value(self):
        model = PyGraphModel()
        model.addNode("math_expresison", "2+5*3", kind='expression')
        self.assertEqual(model.data("math_expresison", 'result'), (None, 17))

    def test_expression_with_X(self):
        model = PyGraphModel()
        model.addNode("math_expresison", "x*3", kind='expression')
        err, value = model.data("math_expresison", 'result')
        self.assertIsInstance(err, NameError)
        self.assertIsNone(value)

    def test_expression_with_inputs(self):
        model = PyGraphModel()
        model.addNode('variable', '5', kind='value')
        model.addNode("math_expresison", "x*3", kind='expression')
        model.linkNodes("variable", 'math_expresison', 'out', 'x')
        self.assertEqual(model.data("math_expresison", 'result'), (None, 15))

    def test_list_comprehension(self):
        model = PyGraphModel()
        model.addNode('variable', '[1, 2]', kind='value')
        model.addNode("list_comprehension", "[x*2 for x in numbers]", kind='expression')
        model.linkNodes("variable", 'list_comprehension', 'out', 'numbers')
        self.assertEqual(model.data("list_comprehension", 'result'), (None, [2, 4]))

    def test_unpacking_comprehension(self):
        model = PyGraphModel()
        model.addNode('variable', "{'a':1, 'b':2}", kind='value')
        model.addNode("dict_comprehension", "[key+str(value) for key, value in d.items()]", kind='expression')
        model.linkNodes("variable", 'dict_comprehension', 'out', 'd')
        self.assertEqual(model.data("dict_comprehension", 'result'), (None, ['a1', 'b2']))

class TestExpressionInlets(unittest.TestCase):
    def test_multiple_occurence(self):
        """test multiple occurance of the same variable"""
        model = PyGraphModel()
        model.addNode("my_pow", "x*x", kind='expression')

        self.assertEqual(model.inlets("my_pow"), ['x'])



# class TestAutoEvaluation(unittest.TestCase):
#     def test_value_change(self):
#         model = PyGraphModel()
#         model.restartKernel(dedent("""\
#         def say_hello(name:str):
#             return f'Hello {name}!'
#         """))
        

#         model.addNode("name", expression="'NAME'", kind="value")
#         self.assertEqual(model.data("name", 'result'), (None, "NAME") )
#         model.setData("name", 'expression', "'Masa'")
#         self.assertEqual(model.data("name", 'result'), (None, "Masa") )

#     def test_dependency_change(self):
#         model = PyGraphModel()
#         model.restartKernel(dedent("""\
#         def say_hello(name:str):
#             return f'Hello {name}!'
#         """))
        

#         model.addNode("name", expression="'NAME'", kind="value")
#         model.addNode("say_hello", expression="say_hello", kind="operator")
#         model.linkNodes("name", "say_hello", "out", "name")

#         data_change_spy = QSignalSpy(model.dataChanged)

#         self.assertEqual(model.data("say_hello", 'result'), (None, "Hello NAME!") )
#         model.setData("name", "expression", "'Mása'")
#         self.assertEqual(model.data("say_hello", 'result'), (None, "Hello Mása!") )


#         self.assertEqual(data_change_spy.count(), 2)

#         for i in range(data_change_spy.count()):
#             emission = data_change_spy.at(i)
#             print("emission", emission)
#         arguments = data_change_spy.at(1)
#         print(arguments)

if __name__ == "__main__":
    unittest.main()