from typing import *
import unittest

from PySide6.QtWidgets import QApplication
from pylive.examples.python_function_graph.python_graph_model import (
    PythonGraphModel,
)


class TextNodeCRUD(unittest.TestCase):
    def setUp(self) -> None:
        self.app = QApplication.instance()
        self.graph = PythonGraphModel()
        self.graph.addNode("x", print)
        return super().setUp()

    def test_create_node(self):
        graph = PythonGraphModel()
        graph.addNode("a", print)
        self.assertIn("a", graph.nodes())

    def test_create_existing_node(self):
        """new nodes must be unique: adding an already existing node should
        raise a ValueError"""
        graph = PythonGraphModel()
        graph.addNode("b", print)
        with self.assertRaises(ValueError):
            graph.addNode("b", len)

    def test_delete_node(self):
        graph = PythonGraphModel()
        graph.addNode("c", print)
        self.assertIn("c", graph.nodes())

        graph.removeNode("c")
        self.assertNotIn("c", graph.nodes())

    def tearDown(self):
        ...
        # del self.app

    def test_set_node_attributes(self):
        """PythonGrpahModel should protect _arguments, and _result node properties"""
        graph = PythonGraphModel()
        graph.addNode("d", print)

        with self.assertRaises(KeyError):
            graph.setNodeProperties("d", _arguments="whatever")
        with self.assertRaises(KeyError):
            graph.setNodeProperties("d", _result="what")


class TextEdgeCRUD(unittest.TestCase):
    def setUp(self) -> None:
        self.app = QApplication.instance()
        return super().setUp()

    def test_create_edge_with_existing_nodes(self):
        from pathlib import Path

        graph = PythonGraphModel()
        graph.addNode("a", Path.cwd)
        graph.addNode("b", print)

        graph.addEdge("a", "b", "args")
        self.assertIn(("a", "b", "args"), graph.edges())

    def test_delete_edge(self):
        from pathlib import Path

        graph = PythonGraphModel()
        graph.addNode("a", Path.cwd)
        graph.addNode("b", print)

        graph.addEdge("a", "b", "args")

        graph.removeEdge("a", "b", "args")
        self.assertNotIn(("a", "b", "args"), graph.edges())

    def create_edge_with_nonexistent_nodes(self):
        graph = PythonGraphModel()

        with self.assertRaises(KeyError):
            graph.addEdge("a", "b", "args")

    def tearDown(self):
        ...
        # del self.app


class TestGraphEvaluation(unittest.TestCase):
    def test_evaluate_single_graph(self):
        from pathlib import Path

        graph = PythonGraphModel()
        graph.addNode("cwd", Path.cwd)
        graph.setOutput("cwd")

        self.assertEqual(graph(), Path.cwd())

    def test_cached_arguments_after_evaluation(self):
        from pathlib import Path

        graph = PythonGraphModel()
        graph.addNode("cwd1", Path.cwd)
        graph.addNode("print1", print)
        graph.addEdge("cwd1", "print1", "args")
        graph.setOutput("print1")

        self.assertEqual(graph(), None)
        self.assertEqual(
            graph.getNodeProperty("print1", "_arguments")["args"], [Path.cwd()]
        )


if __name__ == "__main__":
    unittest.main()
