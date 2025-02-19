from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import unittest
import sys
app= QApplication( sys.argv )

from pylive.VisualCode_v4.graph_editor.graph_data_roles import GraphDataRole
from pylive.VisualCode_v4.py_data_model import PyDataModel, PyNodeItem
from pylive.VisualCode_v4.py_proxy_model import PyNodeProxyModel, PyLinkProxyModel

class TestNodesCRUD(unittest.TestCase):
	def test_init_with_nodes(self) -> None:
		data_model = PyDataModel()
		data_model.addNode("node1", PyNodeItem())

		proxy_model = PyNodeProxyModel(data_model)
		self.assertEqual(proxy_model.rowCount(), 1)
		self.assertEqual(proxy_model.data(proxy_model.index(0,0)), "node1")

	def test_nodes_added(self) -> None:
		data_model = PyDataModel()
		proxy_model = PyNodeProxyModel(data_model)

		data_model.addNode("node1", PyNodeItem())
		self.assertEqual(proxy_model.rowCount(), 1)
		self.assertEqual(proxy_model.data(proxy_model.index(0,0)), "node1")

		data_model.addNode("node2", PyNodeItem())
		self.assertEqual(proxy_model.rowCount(), 2)
		self.assertEqual(proxy_model.data(proxy_model.index(1,0)), "node2")

	def test_remove_last_node(self) -> None:
		data_model = PyDataModel()
		data_model.addNode("node1", PyNodeItem())
		data_model.addNode("node2", PyNodeItem())
		data_model.addNode("node3", PyNodeItem())
		proxy_model = PyNodeProxyModel(data_model)

		data_model.removeNode("node3")
		proxy_names = []
		for row in range(proxy_model.rowCount()):
			index = proxy_model.index(row, 0)
			value = proxy_model.data(index)
			proxy_names.append(value)

		self.assertNotIn("node3", proxy_names)

	def test_remove_first_node(self) -> None:
		data_model = PyDataModel()
		data_model.addNode("node1", PyNodeItem())
		data_model.addNode("node2", PyNodeItem())
		data_model.addNode("node3", PyNodeItem())
		proxy_model = PyNodeProxyModel(data_model)

		data_model.removeNode("node1")
		proxy_names = []
		for row in range(proxy_model.rowCount()):
			index = proxy_model.index(row, 0)
			value = proxy_model.data(index)
			proxy_names.append(value)

		self.assertNotIn("node1", proxy_names)

class TestLinksCRUD(unittest.TestCase):
	def test_read_links(self) -> None:
		data_model = PyDataModel()
		data_model.addNode("node1", PyNodeItem())
		data_model.addNode("node2", PyNodeItem())
		data_model.linkNodes("node1", "node2", "in")

		edges = PyLinkProxyModel(data_model)
		nodes = edges.itemsModel()
		assert nodes
		node1_index = nodes.match(nodes.index(0,0), Qt.ItemDataRole.DisplayRole, "node1", 1, Qt.MatchFlag.MatchExactly)[0]
		node2_index = nodes.match(nodes.index(0,0), Qt.ItemDataRole.DisplayRole, "node2", 1, Qt.MatchFlag.MatchExactly)[0]

		self.assertEqual(edges.rowCount(), 1)
		self.assertEqual(edges.data(edges.index(0,0), GraphDataRole.LinkSourceRole), (node1_index, "out") )
		self.assertEqual(edges.data(edges.index(0,0), GraphDataRole.LinkTargetRole), (node2_index, "in") )

	def test_add_link(self) -> None:
		data_model = PyDataModel()
		proxy_model = PyLinkProxyModel(data_model)
		
		data_model.addNode("node1", PyNodeItem())
		data_model.addNode("node2", PyNodeItem())
		data_model.linkNodes("node1", "node2", "in")

		self.assertEqual(proxy_model.rowCount(), 1)
		self.assertEqual(proxy_model.data(proxy_model.index(0,0)), "node1")
		self.assertEqual(proxy_model.data(proxy_model.index(0,1)), "node2")
		self.assertEqual(proxy_model.data(proxy_model.index(0,2)), "in")

	
			

if __name__ == "__main__":
	unittest.main()