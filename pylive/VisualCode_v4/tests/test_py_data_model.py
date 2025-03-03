from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtTest import QSignalSpy

import unittest
import sys

from yaml import safe_dump
app= QApplication( sys.argv )

from pylive.VisualCode_v4.graph_editor.graph_data_roles import GraphDataRole
from pylive.VisualCode_v4.py_data_model import Empty, PyDataModel, PyNodeDataItem, PyParameterItem

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

    @unittest.skip
    def test_attempt_linking_to_unexisting_nodes_and_inlets(self):
        data_model = PyNodeDataItem()
        data_model.deserialize(math_script)

        with self.assertRaises(ValueError):
            data_model.linkNodes("NOTHING", "mult", "out", "x")

        with self.assertRaises(ValueError):
            data_model.linkNodes("two", "NOTHING", "out", "x")

        with self.assertRaises(ValueError):
            data_model.linkNodes("two", "mult", "out", "NOTHING")

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
            ('two', 'mult', "out", 'x'),
            ('three', 'mult', "out", 'y'),
        })

    def test_remove_node_with_links(self):
        # removing nodes should remove its links too
        data_model = PyDataModel()
        data_model.fromData({
            'nodes':[
                {'name': "A", 'source':"""func(in):    ..."""},
                {'name': "B", 'source':"""func(in):    ..."""},
                {'name': "C", 'source':"""func(in):    ..."""}
            ],

            'edges':[
                {'source': "A", "target": "B", 'inlet':"in"},
                {'source': "B", "target": "C", 'inlet':"in"}
            ]
        })

        nodes_unlinked_spy = QSignalSpy(data_model.nodesUnlinked)
        self.assertEqual(data_model.linkCount(), 2)
        data_model.removeNode("B")
        self.assertEqual(data_model.linkCount(), 0)

        # test signals
        self.assertEqual(nodes_unlinked_spy.count(), 2, "'nodesUnlinked' Signal was not emitted exactly twice.")


class TestSerialization(unittest.TestCase):
    def test_deserialize(self):
        data_model = PyDataModel()
        data_model.deserialize(say_hello_script)

        self.assertEqual(data_model.nodeCount(), 2)
        self.assertEqual(data_model.linkCount(), 1)
        nodes = set(_ for _ in data_model.nodes())
        self.assertEqual(nodes, {'person', 'say_hello'})
        links = {_ for _ in data_model.links()}
        self.assertEqual(links, {('person', 'say_hello', "out", 'name')})

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
        self.assertIn( ("Judit", "say_hello", "out", "name"),  data_model.links())
        
    def test_parameter_link_syntax(self):
        """test support ing parameters with link using @"""

    def test_graph_to_data(self):
        data_model = PyDataModel()
        data_model.addNode("A", 
            source="def read_abstract():  return 'text'", 
        )
        data_model.addNode("B", 
            source="""def to_html(html:str):  return f'HTML({html})'""", 
        )
        data_model.addNode("C", 
            source="""def create_label(text:str):  return QLabel(text)""", 
        )
        # for n in ["A", "B", "C"]:
        #     data_model.compile(n)
        data_model.linkNodes("A", "B", "out", 'html')
        data_model.linkNodes("B", "C", "out", 'text')

        file_data = data_model.toData()
        import yaml

        self.maxDiff = None
        # print(file_data)
        expected_data = {
            'nodes': [
                {'name': 'A', 'source': "def read_abstract():  return 'text'"}, 
                {'name': 'B', 'source': "def to_html(html:str):  return f'HTML({html})'",   'fields': {'html': ' -> A'}}, 
                {'name': 'C', 'source': "def create_label(text:str):  return QLabel(text)", 'fields': {'text': ' -> B'}}
            ]
        }
        self.assertEqual(file_data, expected_data)


class TestCompilation(unittest.TestCase):
    def test_compile_hello_function(self):
        
        data_model = PyDataModel()
        data_model.addNode("hello", source=dedent("""\
        def hello(name:str="you"):
            return f"Hello {name}!"
        """))

        self.assertEqual(data_model.result("hello"), (None, "Hello you!") )

    def test_compile_bad_syntax_function(self):
        from textwrap import dedent
        data_model = PyDataModel()
        data_model.addNode("bad", source="clas bum")

        self.assertIsInstance(data_model.result("bad")[0], SyntaxError)

    def test_compile_no_valid_function(self):
        """if no functions found in the script, raise a ValueError"""
        """currently only functions are supported. TODO: support classes, methods, expressions, values etc.?"""
        from textwrap import dedent
        data_model = PyDataModel()
        data_model.addNode("class_definition", source=dedent("""\
        class Person:
            ...
        """))

        self.assertIsInstance(data_model.result("class_definition")[0], ValueError)




class TestEvaluation(unittest.TestCase):
    def test_evaluate_single_node(self):
        data_model = PyDataModel()
        data_model.addNode("say_hello", source=dedent("""\
        def say_hello():
            return "Hello!"
        """))

        self.assertEqual(data_model.result("say_hello"), (None, "Hello!") )

    def test_evaluate_chain_of_nodes(self):
        data_model = PyDataModel()
        data_model.deserialize(math_script)

        self.assertEqual(data_model.result("mult"), (None, 6) )

    def test_evaluate_node_with_missing_parameters(self):
        data_model = PyDataModel()
        script = dedent("""\
        def say_hello(name:str):
            return "Hello " + name + "!"
        """)
        data_model.addNode("node_with_error", source=script)
        err, result = data_model.result('node_with_error')
        self.assertIsInstance(err, Exception)
        self.assertEqual(err.args[0], "say_hello() missing 1 required positional argument: 'name'")
        # print("!!ARGS!!!!!!!!!!!", node_error.args[0])
        
        # exec(script+"\nsay_hello()")


class TestAutoEvaluation(unittest.TestCase):
    def test_autoevaluate_single_node(self):
        model = PyDataModel()
        model.addNode("say_hello", source="def func():    ...")

        result_spy = QSignalSpy(model.resultsInvaliadated)
        model.setSource("say_hello", dedent("""\
        def say_hello(name:str="You"):
            return f"Hello {name}!"
        """))

        self.assertEqual(model.result("say_hello"), (None, "Hello You!") )
        # self.assertEqual(result_spy.count(), 1)

    def test_dependendts(self):
        model = PyDataModel()
        model.fromData({
            'nodes': [
                {
                    'name': "user",
                    'source': dedent("""\
                        def get_user():
                            return 'name'
                    """)
                },
                {
                    'name': "say_hello",
                    'source': dedent("""\
                        def say_hello(name:str):
                            return f'Hello {name}!'
                    """),
                    'fields':{
                        'name': ' -> user'
                    }
                }
            ]
        })
        model.setSource("user", dedent("""\
            def get_user():
                return 'Mása'
        """))
        self.assertEqual(model.result("user"), (None, 'Mása'))
        self.assertEqual(model.result("say_hello"), (None, 'Hello Mása!'))


if __name__ == "__main__":
    unittest.main()