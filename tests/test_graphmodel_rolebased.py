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
	def setup_graph(self):
		self.graph = GraphModel()
		self.start_node = self.graph.addNode("Start", 5,5)
		self.outlet = self.graph.addOutlet(self.start_node, "out")
		self.finish_node = self.graph.addNode("Finish", 5,5)
		self.inlet = self.graph.addInlet(self.finish_node, "in")
		self.edge = self.graph.addEdge(self.outlet, self.inlet)

	def test_removing_edges(self):
		self.setup_graph()
		self.graph.removeEdges([self.edge])
		self.assertNotIn(self.edge, list(self.graph.getEdges()))

	def test_removing_outlets(self):
		self.setup_graph()
		self.graph.removeOutlets([self.outlet])
		self.assertNotIn(self.outlet, list(self.graph.getOutlets()))

	def test_removing_inlets(self):
		self.setup_graph()
		self.graph.removeInlets([self.inlet])
		self.assertNotIn(self.inlet, list(self.graph.getInlets()))

	def test_removing_inlets_with_connected_edge(self):
		self.setup_graph()
		self.graph.removeInlets([self.inlet])

		self.assertNotIn(self.inlet, list(self.graph.getInlets()))
		self.assertNotIn(self.edge, list(self.graph.getEdges()))

	def test_removing_outlet_with_connected_edge(self):
		self.setup_graph()
		self.graph.removeInlets([self.inlet])

		self.assertNotIn(self.inlet, self.graph.getInlets())
		self.assertNotIn(self.edge, self.graph.getEdges())

	def test_removing_nodes(self):
		self.setup_graph()
		self.graph.removeNodes([self.start_node])
		self.assertNotIn(self.start_node, list(self.graph.getNodes()))

	def test_removing_nodes_with_connected_pins(self):
		self.setup_graph()
		self.graph.removeNodes([self.start_node])

		self.assertNotIn(self.start_node, self.graph.getNodes())
		self.assertNotIn(self.outlet, self.graph.getOutlets())
		self.assertNotIn(self.edge, self.graph.getEdges())

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
		self.assertEqual([idx for idx in outlets], [self.image_out])

	def test_get_node_inlets(self):
		"""node inlets"""
		inlets = self.graph.getNodeInlets(self.write_node)
		self.assertEqual([idx for idx in inlets], [self.image_in])

	def test_get_inlet_owner(self):
		"""inlet owner"""
		owner_node = self.graph.getInletOwner(self.image_in)
		self.assertEqual(owner_node, self.write_node)

	def test_get_inlet_edges(self):
		"""inlet edges"""
		edges = self.graph.getInletEdges(self.image_in)
		self.assertEqual([edge for edge in edges], [self.edge])

	def test_get_outlet_owner(self):
		"""outlet owner"""
		owner_node = self.graph.getOutletOwner(self.image_out)
		self.assertEqual(owner_node, self.read_node)

	def test_get_outlet_edges(self):
		"""outlet edges"""
		edges = self.graph.getOutletEdges(self.image_out)
		self.assertEqual([edge for edge in edges], [self.edge])

	def test_get_edge_source(self):
		"""edge source"""
		self.assertEqual(self.graph.getEdgeSource(self.edge), self.image_out)

	def test_get_edge_target(self):
		"""edge target"""
		self.assertEqual(self.graph.getEdgeTarget(self.edge), self.image_in)

from PySide6.QtTest import QSignalSpy
class TestGraphModelSignals(unittest.TestCase):
	def setup_graph(self):
		self.graph = GraphModel()
		self.start_node = self.graph.addNode("Start", 5,5)
		self.outlet = self.graph.addOutlet(self.start_node, "out")
		self.outlet2 = self.graph.addOutlet(self.start_node, "out2")
		self.finish_node = self.graph.addNode("Finish", 5,5)
		self.inlet = self.graph.addInlet(self.finish_node, "in")

		self.edge = self.graph.addEdge(self.outlet, self.inlet)

	def test_nodes_added(self):
		self.setup_graph()
		spy = QSignalSpy(self.graph.nodesAdded)
		self.graph.addNode("a new node", 0, 0)
		self.assertEqual(spy.count(), 1, "'nodesAdded' Signal was not emitted exactly once.")

	def test_nodes_removed(self):
		self.setup_graph()
		spy = QSignalSpy(self.graph.nodesAboutToBeRemoved)
		self.graph.removeNodes([self.start_node])
		self.assertEqual(spy.count(), 1, "'nodesAboutToBeRemoved' Signal was not emitted exactly once.")

	def test_nodes_changed(self):
		pass

	def test_inlets_added(self):
		self.setup_graph()
		spy = QSignalSpy(self.graph.inletsAdded)
		self.graph.addInlet(self.start_node, "inlet")
		self.assertEqual(spy.count(), 1, "'inletsAdded' Signal was not emitted exactly once.")

	def test_inlets_removed(self):
		self.setup_graph()
		spy = QSignalSpy(self.graph.inletsAboutToBeRemoved)
		self.graph.removeInlets([self.inlet])
		self.assertEqual(spy.count(), 1, "'inletsAboutToBeRemoved' Signal was not emitted exactly once.")

	def test_inlets_changed(self):
		pass

	def test_outlets_added(self):
		self.setup_graph()
		spy = QSignalSpy(self.graph.outletsAdded)
		self.graph.addOutlet(self.finish_node, "outlet")
		self.assertEqual(spy.count(), 1, "'outletsAdded' Signal was not emitted exactly once.")

	def test_outlets_removed(self):
		self.setup_graph()
		spy = QSignalSpy(self.graph.outletsAboutToBeRemoved)
		self.graph.removeOutlets([self.outlet])
		self.assertEqual(spy.count(), 1, "'outletsAboutToBeRemoved' Signal was not emitted exactly once.")

	def test_outlets_changed(self):
		pass

	def test_edges_added(self):
		self.setup_graph()
		spy = QSignalSpy(self.graph.edgesAdded)
		new_edge = self.graph.addEdge(self.outlet2, self.inlet)
		self.assertEqual(spy.count(), 1, "'edgesAdded' Signal was not emitted exactly once.")

	def test_edges_removed(self):
		self.setup_graph()
		spy = QSignalSpy(self.graph.edgesAboutToBeRemoved)
		self.graph.removeEdges([self.edge])
		self.assertEqual(spy.count(), 1, "'edgesAboutToBeRemoved' Signal was not emitted exactly once.")

	@unittest.skip("Edges has no data assigned yet other then the source and target pins")
	def test_edges_changed(self):
		raise NotImplementedError()


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
	