from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtTest import QSignalSpy

import unittest
import sys

from yaml import safe_dump
app= QApplication( sys.argv )

from pylive.VisualCode_v6.py_graph_model import PyGraphModel


from textwrap import dedent

from pathlib import Path
tests_folder = Path(__file__).parent.resolve()


class TestEvaluation(unittest.TestCase):
    def test_values(self):
        graph = PyGraphModel()
        graph.addValue("two", 2)
        graph.addValue("three", 3)

        self.assertEqual(graph.data('two', 'result'), (None, 2) )

    def test_operator(self):
        import operator
        graph = PyGraphModel()
        graph.addValue("two", 2)
        graph.addValue("three", 3)
        graph.addFunction("mul", operator.mul)
        graph.linkNodes("two", "mul", "out", "a")
        graph.linkNodes("three", "mul", "out", "b")

        self.assertEqual(graph.data('mul', 'result'), (None, 6) )

if __name__ == "__main__":
    unittest.main()