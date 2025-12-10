"""
# NXNetowrkModel Tests

1. Test if network model behaves the same as a NXGraphmodel
     - except for the edge key:
     - it must throw errors, when the edge key is not a tuple specifying the
         connected inlets or edges
2. inlets outlets tests
     - either auto create outlets and inlets (like networkx autocreate nodes when
         edges are added)
     - or throw an error when the ports does not exist.
"""

import unittest
from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel


class TestNodeCRUD(unittest.TestCase):
    def setUp(self) -> None:
        self.app = QApplication.instance()
        return super().setUp()

    def test_create_node(self):
        graph = NXGraphModel()
        graph.addNode("n1")
        self.assertIn("n1", graph.nodes())

    def test_adding_unique_nodes(self):
        """adding new functions must have unique id"""
        graph = NXGraphModel()
        graph.addNode("n1")
        with self.assertRaises(ValueError):
            graph.addNode("n1")

    def test_delete_node(self):
        """adding new functions must have unique id"""
        graph = NXGraphModel()
        graph.addNode("n1")
        self.assertIn("n1", graph.nodes())

        graph.removeNode("n1")
        self.assertNotIn("n1", graph.nodes())
        
    def tearDown(self):
        ...
        # del self.app


class TextEdgeCRUD(unittest.TestCase):
    def setUp(self) -> None:
        self.app = QApplication.instance()
        return super().setUp()

    def test_create_edge_with_existing_nodes(self):
        from pathlib import Path

        graph = NXGraphModel()
        graph.addNode("a")
        graph.addNode("b")

        graph.addEdge("a", "b", 0)
        self.assertIn(("a", "b", 0), graph.edges())

    def test_delete_edge(self):
        from pathlib import Path

        graph = NXGraphModel()
        graph.addNode("a")
        graph.addNode("b")

        graph.addEdge("a", "b", 0)

        graph.removeEdge("a", "b", 0)
        self.assertNotIn(("a", "b", 0), graph.edges())

    def create_edge_with_nonexistent_nodes(self):
        graph = NXGraphModel()
        with self.assertRaises(KeyError):
            graph.addEdge("a", "b", "args")

    def tearDown(self):
        ...
        # del self.app


class TestNodeAttributesCRUD(unittest.TestCase):
    def setUp(self) -> None:
        ...

    def test_initial_attributes(self):
        graph = NXGraphModel()
        graph.addNode("N1", hello="VALUE")
        self.assertEqual(graph.getNodeAttribute("N1", "hello"), "VALUE")

    def test_attribute_added(self):
        graph = NXGraphModel()
        graph.addNode("N1", hello="VALUE")
        graph.updateNodeAttributes("N1", hello2="VALUE2")
        self.assertEqual(graph.getNodeAttribute("N1", "hello2"), "VALUE2")

    def test_attribute_updated(self):
        graph = NXGraphModel()
        graph.addNode("N1", hello="VALUE")
        graph.updateNodeAttributes("N1", hello="VALUE2")
        self.assertEqual(graph.getNodeAttribute("N1", "hello"), "VALUE2")

    def test_attribute_delete(self):
        graph = NXGraphModel()
        graph.addNode("N1", hello="VALUE")
        graph.deleteNodeAttribute("N1", "hello")
        with self.assertRaises(KeyError):
            value = graph.getNodeAttribute("N1", "hello")


from PySide6.QtTest import QSignalSpy

class TestNodeAttributeSignals(unittest.TestCase):
    def test_attribute_added(self):
        graph = NXGraphModel()
        graph.addNode("N1", hello="VALUE")
        spy = QSignalSpy(graph.nodeAttributesAdded)
        graph.updateNodeAttributes("N1", prop2="VALUE2")
        self.assertEqual(spy.count(), 1, "Signal 'nodeAttributesAdded' was not emitted exactly once.")
        self.assertEqual(spy.at(0)[0], {"N1": ["prop2"]})

    def test_attribute_updated(self):
        graph = NXGraphModel()
        graph.addNode("N1", prop="VALUE")
        spy = QSignalSpy(graph.nodeAttributesChanged)
        graph.updateNodeAttributes("N1", prop="VALUE2")
        self.assertEqual(spy.count(), 1, "Signal 'nodeAttributesChanged' was not emitted exactly once.")
        self.assertEqual(spy.at(0)[0], {"N1": ["prop"] })

    def test_attribute_deleted(self):
        graph = NXGraphModel()
        graph.addNode("N1", hello="VALUE")
        spy = QSignalSpy(graph.nodeAttributesRemoved)
        graph.deleteNodeAttribute("N1", "hello")

        self.assertEqual(spy.count(), 1, "Signal 'nodeAttributesRemoved' was not emitted exactly once.")
        self.assertEqual(spy.at(0)[0], {"N1": ["hello"] })


# TODO: test edge attributes!
class TestEdgeAttributesCRUD(unittest.TestCase):
    def setUp(self) -> None:
        ...

    def test_initial_attributes(self):
        ...

    def test_attribute_added(self):
        ...

    def test_attribute_updated(self):
        ...

    def test_attribute_delete(self):
        ...


class TestNodeParents(unittest.TestCase):
    def setUp(self) -> None:
        self.app = QApplication.instance()
        return super().setUp()

    def test_create_child_node(self):
        graph = NXGraphModel()
        graph.addNode("n1")
        graph.addNode("child", parent="n1")

        self.assertEqual(graph.parentNode("child"), "n1")
        self.assertIn("child", [_ for _ in graph.childNodes("n1")])

    def test_adding_child_to_unexisting_parent(self):
        graph = NXGraphModel()
        with self.assertRaises(KeyError):
            graph.addNode("child", parent="n1")

        # del self.app


if __name__ == "__main__":
    unittest.main()