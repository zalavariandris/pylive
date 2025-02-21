
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtTest import *

import unittest
import sys
app = QApplication( sys.argv )

from pylive.VisualCode_v4.graph_editor.graph_editor_view import GraphEditorView
from pylive.VisualCode_v4.graph_editor.standard_edges_model import StandardEdgeItem, StandardEdgesModel

class MyNodesModel(QStandardItemModel):
    def __init__(self, parent:QObject|None=None):
        super().__init__(parent)

    def inlets(self, row:int)->Sequence[str]:
        return ["in"]

    def outlets(self, row:int)->Sequence[str]:
        return ["out"]


class TestNodeCRUD(unittest.TestCase):
    def setUp(self) -> None:
        self.nodes = MyNodesModel()
        self.edges = StandardEdgesModel(nodes=self.nodes)
        self.view = GraphEditorView()
        self.view.setModel(self.nodes, self.edges)
        self.view.show()

        item1 = QStandardItem("node1")
        item2 = QStandardItem("node2")
        self.nodes.appendRow(item1)
        self.nodes.appendRow(item2)
        node_index1 = self.nodes.indexFromItem(item1)
        node_index2 = self.nodes.indexFromItem(item2)

    def test_widget_created_on_node_insert(self):
        item = QStandardItem("N")
        self.nodes.appendRow(item)
        index = self.nodes.indexFromItem(item)
        self.assertEqual(self.nodes.rowCount(), len(self.view.nodeWidgets()))
        self.assertIsNotNone(self.view.nodeWidget(index))

    def test_widget_removed_on_node_remove(self):
        index = self.nodes.index(0, 0)
        node_widget = self.view.nodeWidget(index)
        self.nodes.removeRow(index.row())
        
        self.assertEqual(self.nodes.rowCount(), len(self.view.nodeWidgets()))
        self.assertNotIn(node_widget, self.view.nodeWidgets())


class TestEdgeCRUD(unittest.TestCase):
    def setUp(self) -> None:
        self.nodes = MyNodesModel()
        self.edges = StandardEdgesModel(nodes=self.nodes)
        self.view = GraphEditorView()
        self.view.setModel(self.nodes, self.edges)
        self.view.show()

        item1 = QStandardItem("node1")
        item2 = QStandardItem("node2")
        self.nodes.appendRow(item1)
        self.nodes.appendRow(item2)
        node_index1 = self.nodes.indexFromItem(item1)
        node_index2 = self.nodes.indexFromItem(item2)
        edge_item = StandardEdgeItem(
            QPersistentModelIndex(node_index1), 
            QPersistentModelIndex(node_index2), 
            "out", 
            "in"
        )
        self.edges.appendEdgeItem(edge_item)
        edge_index = self.edges.indexFromEdgeItem(edge_item)
        
    def test_widget_created_on_edge_insert(self):
        item1 = QStandardItem("N1")
        self.nodes.appendRow(item1)
        index1 = self.nodes.indexFromItem(item1)
        item2 = QStandardItem("N2")
        self.nodes.appendRow(item2)
        index2 = self.nodes.indexFromItem(item2)

        edge_item = StandardEdgeItem(
            QPersistentModelIndex(index1), 
            QPersistentModelIndex(index2), 
            "out", 
            "in"
        )
        self.edges.appendEdgeItem(edge_item)
        edge_index = self.edges.indexFromEdgeItem(edge_item)

        self.assertIsNotNone(self.view.linkWidget(edge_index))

    def test_widget_removed_on_edge_remove(self):
        edge_index = self.edges.index(0, 0)
        edge_widget = self.view.linkWidget(edge_index)
        assert self.edges.rowCount()>0
        self.edges.removeRow(0)
        self.assertEqual(self.edges.rowCount(), len(self.view.edgeWidgets()) )
        self.assertNotIn(edge_widget, self.view.edgeWidgets())


    

if __name__ == "__main__":
    unittest.main()