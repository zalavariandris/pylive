from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import unittest
import sys

from yaml import safe_dump
app= QApplication( sys.argv )

from pylive.VisualCode_v4.graph_editor.graph_data_roles import GraphDataRole
from pylive.VisualCode_v4.py_data_model import Empty, PyDataModel, PyNodeItem, PyParameterItem

import inspect

from textwrap import dedent

from pathlib import Path
tests_folder = Path(__file__).parent.resolve()
math_script = (tests_folder/"math_script.yaml").read_text()
say_hello_script = (tests_folder/"say_hello_script.yaml").read_text()


class TestModelCRUD(unittest.TestCase):
    def test_read(self):
        ...

    def test_create_node(self):
        ...

    def test_attempt_linking_to_unexisting_nodes_and_inlets(self):
        data_model = PyDataModel()
        data_model.deserialize(math_script)

        with self.assertRaises(ValueError):
            data_model.linkNodes("NOTHING", "mult", "x")

        with self.assertRaises(ValueError):
            data_model.linkNodes("two", "NOTHING", "x")

        with self.assertRaises(ValueError):
            data_model.linkNodes("two", "mult", "NOTHING")

    def test_create_link(self):
        ...

    def test_delete_link(self):
        ...

    def test_create_parameter(self):
        ...

    def test_delete_parameter(self):
        ...

    def test_reset(self):
        data_model = PyDataModel()
        data_model.deserialize(say_hello_script)

        data_model.deserialize(math_script)
        self.assertEqual(data_model.nodeCount(), 3)
        self.assertEqual(data_model.linkCount(), 2)
        nodes = set(_ for _ in data_model.nodes())
        self.assertEqual(nodes, {'two', 'three', 'mult'})
        links = {_ for _ in data_model.links()}
        self.assertEqual(links, {
            ('two', 'mult', 'x'),
            ('three', 'mult', 'y'),
        })

class TestSerialization(unittest.TestCase):
    def test_deserialize(self):
        data_model = PyDataModel()
        data_model.deserialize(say_hello_script)

        self.assertEqual(data_model.nodeCount(), 2)
        self.assertEqual(data_model.linkCount(), 1)
        nodes = set(_ for _ in data_model.nodes())
        self.assertEqual(nodes, {'person', 'say_hello'})
        links = {_ for _ in data_model.links()}
        self.assertEqual(links, {('person', 'say_hello', 'name')})

    def test_explicit_edges(self):
        """test support edges defined under 'edges'"""
        data_model = PyDataModel()
        data_model.deserialize("""\
        nodes:
        - name: Judit
          source: |
            def Judit():
              return 'Judit'

        - name: say_hello
          source: |
            def say_hello(name:str):
              return f"Hello {name}!"
          fields:
            name: -> Judit
        """)

        self.assertEqual(data_model.linkCount(), 1)
        self.assertIn( ("Judit", "say_hello", "name"),  data_model.links())
        
    def test_parameter_link_syntax(self):
        """test support ing parameters with link using @"""


class TestCompilation(unittest.TestCase):
    def test_compile_hello_function(self):
        
        data_model = PyDataModel()
        data_model.addNode("hello", PyNodeItem(source=dedent("""\
        def hello(name:str="you"):
            return f"Hello {name}"
        """)))

        success = data_model.compileNodes(["hello"])
        self.assertTrue(data_model.isCompiled("hello"))

    def test_compile_bad_syntax_function(self):
        from textwrap import dedent
        data_model = PyDataModel()
        data_model.addNode("bad", PyNodeItem(source="clas bum"))

        success = data_model.compileNodes(["bad"])
        self.assertFalse(success)
        self.assertFalse(data_model.isCompiled("bad"))
        self.assertIsNotNone(data_model.nodeError("bad"))
        self.assertIsInstance(data_model.nodeError("bad"), SyntaxError)

    def test_compile_no_valid_function(self):
        """if no functions found in the script, raise a ValueError"""
        """currently only functions are supported. TODO: support classes, methods, expressions, values etc.?"""
        from textwrap import dedent
        data_model = PyDataModel()
        data_model.addNode("class_definition", PyNodeItem(source=dedent("""\
        class Person:
            ...
        """)))

        success = data_model.compileNodes(["class_definition"])
        self.assertFalse(success)
        self.assertFalse(data_model.isCompiled("class_definition"))
        self.assertIsNotNone(data_model.nodeError("class_definition"))
        self.assertIsInstance(data_model.nodeError("class_definition"), ValueError)


class TestParametersCRUD(unittest.TestCase):
    def test_init_with_empty_parameters(self):
        data_model = PyDataModel()
        data_model.addNode("node1", PyNodeItem(parameters=[
            PyParameterItem("input1"),
            PyParameterItem("input2")
        ]))

        self.assertEqual(data_model.parameterCount("node1"), 2)

        param1 = data_model.parameterItem("node1", 0)
        param2 = data_model.parameterItem("node1", 1)
        self.assertEqual(param1.name, "input1")
        self.assertEqual(param2.name, "input2")

    def test_compile_parameters(self):
        from textwrap import dedent
        data_model = PyDataModel()
        data_model.addNode("hello", PyNodeItem(source=dedent("""\
        def hello(name:str="you"):
            return f"Hello {name}"
        """)))
        # data_model.addNode("bad_function", PyNodeItem(source=dedent("""\
        # de
        # """)))

        data_model.compileNodes(["hello"])
        self.assertEqual(data_model.parameterCount("hello"), 1)
        param_item = data_model.parameterItem("hello", 0)
        self.assertEqual(param_item.name, "name")
        self.assertEqual(param_item.annotation, str)
        self.assertEqual(param_item.default, "you")
        self.assertEqual(param_item.value, inspect.Parameter.empty)
        self.assertEqual(param_item.kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)

    def test_compile_parameters_with_stored_values(self):
        from textwrap import dedent
        data_model = PyDataModel()
        data_model.addNode("hello", PyNodeItem(
            source=dedent("""\
                def hello(name:str="you"):
                    return f"Hello {name}"
                """),
            parameters=[PyParameterItem(name="name", value="Mása")]
        ))

        data_model.compileNodes(["hello"])
        self.assertEqual(data_model.parameterCount("hello"), 1)
        param_item = data_model.parameterItem("hello", 0)
        self.assertEqual(param_item.default, "you")
        self.assertEqual(param_item.value, "Mása")
        data_model = PyDataModel()
        data_model.addNode("node1", PyNodeItem(parameters=[
            PyParameterItem("input1"),
            PyParameterItem("input2")
        ]))

    def test_empty_parameters(self):
        data_model = PyDataModel()
        script = dedent("""\
        def say_hello(name:str):
            return "Hello " + name + "!"
        """)
        data_model.addNode("node_with_error", PyNodeItem(source=script))
        data_model.compileNodes(['node_with_error'])
        self.assertEqual(data_model.parameterValue('node_with_error', 0), Empty)

class TestEvaluation(unittest.TestCase):
    def test_evaluate_single_node(self):
        data_model = PyDataModel()
        data_model.addNode("say_hello", PyNodeItem(source=dedent("""\
        def say_hello():
            return "Hello!"
        """)))

        data_model.evaluateNodes(['say_hello'])
        self.assertIsNone(data_model.nodeError("say_hello"))
        self.assertTrue(data_model.isCompiled("say_hello"))
        self.assertTrue(data_model.isEvaluated("say_hello"))
        self.assertEqual(data_model.nodeResult("say_hello"), "Hello!")

    def test_evaluate_chain_of_nodes(self):
        data_model = PyDataModel()
        data_model.deserialize(math_script)

        data_model.evaluateNodes(['mult'])

        self.assertEqual(data_model.nodeResult("mult"), 6)
        
    

    def test_evaluate_node_with_missing_parameters(self):
        data_model = PyDataModel()
        script = dedent("""\
        def say_hello(name:str):
            return "Hello " + name + "!"
        """)
        data_model.addNode("node_with_error", PyNodeItem(source=script))
        data_model.evaluateNodes(["node_with_error"])
        node_error:Exception|None = data_model.nodeError('node_with_error')
        self.assertIsInstance(node_error, TypeError)
        assert isinstance(node_error, TypeError)
        self.assertEqual(node_error.args[0], "say_hello() missing 1 required positional argument: 'name'")
        # print("!!ARGS!!!!!!!!!!!", node_error.args[0])
        
        # exec(script+"\nsay_hello()")

        
if __name__ == "__main__":
    unittest.main()