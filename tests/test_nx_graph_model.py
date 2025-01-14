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

class TestGraphPropertiesCRUD(unittest.TestCase):
    def setUp(self) -> None:
        ...

    def test_initial_properties(self):
        graph = NXGraphModel()
        graph.addNode("N1", hello="VALUE")
        self.assertEqual(graph.getNodeProperty("N1", "hello"), "VALUE")

    def test_property_added(self):
        graph = NXGraphModel()
        graph.addNode("N1", hello="VALUE")
        graph.updateNodeProperties("N1", hello2="VALUE2")
        self.assertEqual(graph.getNodeProperty("N1", "hello2"), "VALUE2")

    def test_property_updated(self):
        graph = NXGraphModel()
        graph.addNode("N1", hello="VALUE")
        graph.updateNodeProperties("N1", hello="VALUE2")
        self.assertEqual(graph.getNodeProperty("N1", "hello"), "VALUE2")

    def test_property_removed(self):
        ...

from PySide6.QtTest import QSignalSpy
class TestGraphPropertySignals(unittest.TestCase):
    def test_property_added(self):
        graph = NXGraphModel()
        graph.addNode("N1", hello="VALUE")
        spy = QSignalSpy(graph.nodesPropertiesChanged)
        graph.updateNodeProperties("N1", prop2="VALUE2")
        self.assertEqual(spy.count(), 1, "'nodesPropertiesChanged' Signal was not emitted exactly once.")
        self.assertEqual(spy.at(0)[0], {"N1": ["prop2"]})

    def test_property_updated(self):
        graph = NXGraphModel()
        graph.addNode("N1", prop="VALUE")
        spy = QSignalSpy(graph.nodesPropertiesChanged)
        graph.updateNodeProperties("N1", prop="VALUE2")
        self.assertEqual(spy.count(), 1, "'nodesPropertiesChanged' Signal was not emitted exactly once.")
        self.assertEqual(spy.at(0)[0], {"N1": ["prop"] })

    def test_property_removed(self):
        ...

if __name__ == "__main__":
    unittest.main()