import unittest
from graphmodel_rolebased import GraphModel, NodeDataRole, InletDataRole, OutletDataRole, EdgeDataRole

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from typing import *


class TestGraphCreations(unittest.TestCase):
	def test_create_nodes(self):
		graph = GraphModel()
		node = graph.addNode("<name>", 5,5)
		self.assertIn(node, [node for node in graph.getNodes()])

	def test_create_outlet(self):
		graph = GraphModel()
		node = graph.addNode("<name>", 5,5)
		outlet = graph.addOutlet(node, "out")
		self.assertIn(outlet, [outlet for outlet in graph.getOutlets()])
		self.assertIn(outlet, [outlet for outlet in graph.getNodeOutlets(node)])

	def test_create_inlet(self):
		graph = GraphModel()
		node = graph.addNode("<name>", 5,5)
		inlet = graph.addInlet(node, "in")
		self.assertIn(inlet, [inlet for inlet in graph.getInlets()])
		self.assertIn(inlet, [inlet for inlet in graph.getNodeInlets(node)])

	def test_create_edge(self):
		graph = GraphModel()
		start_node = graph.addNode("Start", 5,5)
		outlet = graph.addOutlet(start_node, "out")
		finish_node = graph.addNode("Finish", 5,5)
		inlet = graph.addInlet(finish_node, "in")

		edge = graph.addEdge(outlet, inlet)


		self.assertIn(edge, [edge for edge in graph.getEdges()])
		self.assertIn(edge, [edge for edge in graph.getInletEdges(inlet)])
		self.assertIn(edge, [edge for edge in graph.getOutletEdges(outlet)])
		self.assertEqual(inlet,  graph.getEdgeTarget(edge) )
		self.assertEqual(outlet, graph.getEdgeSource(edge) )


class TestGraphDeletions(unittest.TestCase):
	pass


class TestGraphData(unittest.TestCase):
	def setUp(self) -> None:
		self.graph = GraphModel()
		self.read_node = self.graph.addNode("read", 0,0)
		self.image_out = self.graph.addOutlet(self.read_node, "image_out")
		self.write_node = self.graph.addNode("write", 0,0)
		self.image_in = self.graph.addInlet(self.write_node, "image_in")
		self.edge = self.graph.addEdge(self.image_out, self.image_in)
		return super().setUp()

	def tearDown(self) -> None:
		return super().tearDown()

	def test_get_node_data(self):
		name = self.graph.getNodeData(self.read_node, role=NodeDataRole.NameRole)
		pos = self.graph.getNodeData(self.read_node, role=NodeDataRole.LocationRole)

		self.assertEqual(name, "read")
		self.assertEqual(pos, (0,0) )

	def test_get_inlet_data(self):
		inlet_name = self.graph.getInletData(self.image_in, role=InletDataRole.NameRole)
		self.assertEqual(inlet_name, "image_in")

	def test_get_outlet_date(self):
		outlet_name = self.graph.getOutletData(self.image_out, role=OutletDataRole.NameRole)
		self.assertEqual(outlet_name, "image_out")


class TestGraphRelations(unittest.TestCase):
	def setUp(self) -> None:
		self.graph = GraphModel()
		self.read_node = self.graph.addNode("read", 0,0)
		self.image_out = self.graph.addOutlet(self.read_node, "image_out")
		self.write_node = self.graph.addNode("write", 0,0)
		self.image_in = self.graph.addInlet(self.write_node, "image_in")
		self.edge = self.graph.addEdge(self.image_out, self.image_in)
		return super().setUp()

	def tearDown(self) -> None:
		return super().tearDown()

	def test_get_node_outlets(self):
		"""node outlets"""
		outlets = self.graph.getNodeOutlets(self.read_node)
		self.assertEqual([QPersistentModelIndex(idx) for idx in outlets], [QPersistentModelIndex(self.image_out)])

	def test_get_node_inlets(self):
		"""node inlets"""
		inlets = self.graph.getNodeInlets(self.write_node)
		self.assertEqual([QPersistentModelIndex(idx) for idx in inlets], [QPersistentModelIndex(self.image_in)])

	def test_get_inlet_owner(self):
		"""inlet owner"""
		owner_node = self.graph.getInletOwner(self.image_in)
		self.assertEqual(QPersistentModelIndex(owner_node), QPersistentModelIndex(self.write_node))

	def test_get_inlet_edges(self):
		"""inlet edges"""
		edges = self.graph.getInletEdges(self.image_in)
		self.assertEqual([QPersistentModelIndex(edge) for edge in edges], [QPersistentModelIndex(self.edge)])

	def test_get_outlet_owner(self):
		"""outlet owner"""
		owner_node = self.graph.getOutletOwner(self.image_out)
		self.assertEqual(QPersistentModelIndex(owner_node), QPersistentModelIndex(self.read_node))

	def test_get_outlet_edges(self):
		"""outlet edges"""
		edges = self.graph.getOutletEdges(self.image_out)
		self.assertEqual([QPersistentModelIndex(edge) for edge in edges], [QPersistentModelIndex(self.edge)])

	def test_get_edge_source(self):
		"""edge source"""
		self.assertEqual(self.graph.getEdgeSource(self.edge), self.image_out)

	def test_get_edge_target(self):
		"""edge target"""
		self.assertEqual(self.graph.getEdgeTarget(self.edge), self.image_in)


class TestGraphModelDFS(unittest.TestCase):
	def setUp(self) -> None:
		self.graph = GraphModel()
		self.start_node = self.graph.addNode("Start", 0,0)
		self.graph.addInlet(self.start_node, "in")
		self.outlet = self.graph.addOutlet(self.start_node, "out")

		self.finish_node = self.graph.addNode("Finish", 0,0)
		self.inlet = self.graph.addInlet(self.finish_node, "in")
		self.finish_outlet = self.graph.addOutlet(self.finish_node, "out")

		self.graph.addEdge(self.outlet, self.inlet)
		return super().setUp()

	def test_get_target_nodes(self):
		node_outlets = self.graph.getNodeOutlets(self.finish_node)
		self.assertEqual(len(node_outlets), 1)
		self.assertEqual(node_outlets[0].model(), self.finish_outlet.model())
		self.assertEqual(node_outlets[0], self.finish_outlet)

		target_nodes = self.graph.getTargetNodes(self.finish_node)
		self.assertEqual(len(list(target_nodes)), 0)

	def test_root_nodes(self):
		self.assertEqual(set(list(self.graph.rootRodes())), {self.finish_node})


"""
test if related inlets, edges etc are get removed when nodes are removed
"""


if __name__ == "__main__":
	unittest.main()
	