import unittest
from GraphModel import GraphModel

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from typing import *

class TestGraphModel(unittest.TestCase):
	def setUp(self) -> None:
		self.graph = GraphModel()
		self.read_node = self.graph.addNode("read", 0,0,"")
		self.image_out = self.graph.addOutlet(self.read_node, "image_out")
		self.write_node = self.graph.addNode("write", 0,0,"")
		self.image_in = self.graph.addInlet(self.write_node, "image_in")
		self.edge = self.graph.addEdge(self.image_out, self.image_in)
		return super().setUp()

	def tearDown(self) -> None:
		return super().tearDown()

	def test_get_node(self):
		properties = self.graph.getNode(self.read_node, relations=False)

		self.assertEqual(properties["name"], "read")
		self.assertEqual(properties["posx"], 0)
		self.assertEqual(properties["posy"], 0)

	def test_get_node_relations(self):
		properties = self.graph.getNode(self.read_node, relations=True)
		self.assertEqual([QPersistentModelIndex(idx) for idx in properties["outlets"]], [QPersistentModelIndex(self.image_out)])

		properties = self.graph.getNode(self.write_node, relations=True)
		self.assertEqual([QPersistentModelIndex(idx) for idx in properties["inlets"]], [QPersistentModelIndex(self.image_in)])

	def test_get_inlet(self):
		properties = self.graph.getInlet(self.image_in, relations=False)
		self.assertEqual(properties["name"], "image_in")

	def test_get_inlet_relations(self):
		properties = self.graph.getInlet(self.image_in, relations=True)
		self.assertEqual(QPersistentModelIndex(properties["node"]), QPersistentModelIndex(self.write_node))
		self.assertEqual(properties["edges"], [self.edge])

	def test_get_outlet(self):
		properties = self.graph.getOutlet(self.image_out, relations=False)
		self.assertEqual(properties["name"], "image_out")

	def test_get_outlet_relations(self):
		properties = self.graph.getOutlet(self.image_out, relations=True)
		self.assertEqual(QPersistentModelIndex(properties["node"]), QPersistentModelIndex(self.read_node))
		self.assertEqual(properties["edges"], [self.edge])

	def test_get_edge_relations(self):
		properties = self.graph.getEdge(self.edge, relations=True)
		self.assertEqual(properties["source"], self.image_out)
		self.assertEqual(properties["target"], self.image_in)

if __name__ == "__main__":
	unittest.main()