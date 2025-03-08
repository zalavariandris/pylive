from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtTest import QSignalSpy

import unittest
import sys

from pylive.VisualCode_v6.py_graph_model import PyGraphModel
from textwrap import dedent

class TestEvaluation(unittest.TestCase):
    def test_operator(self):
        model = PyGraphModel()
        model.restartKernel(dedent("""\
        def say_hello(name:str):
            return f'Hello {name}!'
        """))
        

        model.addNode("name", expression="'Mása'", kind="value")
        model.addNode("say_hello", expression="say_hello", kind="operator")
        model.linkNodes("name", "say_hello", "out", "name")


        self.assertEqual(model.data("say_hello", 'result'), (None, "Hello Mása!") )
        # self.assertEqual(result_spy.count(), 1)

class TestAutoEvaluation(unittest.TestCase):
    def test_value_change(self):
        model = PyGraphModel()
        model.restartKernel(dedent("""\
        def say_hello(name:str):
            return f'Hello {name}!'
        """))
        

        model.addNode("name", expression="'NAME'", kind="value")
        self.assertEqual(model.data("name", 'result'), (None, "NAME") )
        model.setData("name", 'expression', "'Masa'")
        self.assertEqual(model.data("name", 'result'), (None, "Masa") )

    def test_dependency_change(self):
        model = PyGraphModel()
        model.restartKernel(dedent("""\
        def say_hello(name:str):
            return f'Hello {name}!'
        """))
        

        model.addNode("name", expression="'NAME'", kind="value")
        model.addNode("say_hello", expression="say_hello", kind="operator")
        model.linkNodes("name", "say_hello", "out", "name")

        data_change_spy = QSignalSpy(model.dataChanged)

        self.assertEqual(model.data("say_hello", 'result'), (None, "Hello NAME!") )
        model.setData("name", "expression", "'Mása'")
        self.assertEqual(model.data("say_hello", 'result'), (None, "Hello Mása!") )


        self.assertEqual(data_change_spy.count(), 2)

        for i in range(data_change_spy.count()):
            emission = data_change_spy.at(i)
            print("emission", emission)
        arguments = data_change_spy.at(1)
        print(arguments)

if __name__ == "__main__":
    unittest.main()