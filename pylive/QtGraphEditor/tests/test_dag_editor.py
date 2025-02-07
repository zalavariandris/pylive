
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtTest import *

import unittest
import sys
app= QApplication( sys.argv )

from pylive.QtGraphEditor.dag_editor_view import DAGEditorView
from pylive.QtGraphEditor.edges_model import EdgeItem, EdgesModel


class TestValidInletDrags(unittest.TestCase):
    def setUp(self):
        ### model state
        self.nodes = QStandardItemModel()
        self.edges = EdgesModel(nodes=self.nodes)
        self.view = DAGEditorView()
        self.view.setModel(self.nodes, self.edges)
        self.view.show()

        self.addNode("node1", ["in1"], ["out"], QPoint(0, 100))
        self.addNode("node2", ["in1"], ["out"], QPoint(0, -100))


    def addNode(self, name:str, inlets:list[str], outlets:list[str], pos:QPoint):
        item = QStandardItem()
        item.setData(name, Qt.ItemDataRole.EditRole)
        item.setData(inlets, DAGEditorView.InletsRole)
        item.setData(outlets, DAGEditorView.OutletsRole)
        row = self.nodes.rowCount()
        self.nodes.insertRow(row, item)
        widget = self.view.nodeWidget(self.nodes.index(row, 0))
        assert widget
        widget.setPos(pos)


    def test_dragging_inlet_to_empty(self):
        """
        # How to simulate a drag and drop action using QTest
        <https://stackoverflow.com/questions/58317816/how-to-simulate-a-drag-and-drop-action-using-qtest>
        """
        inlet = self.view.inletWidget(self.nodes.index(0,0), "in1")
        assert inlet
        self.view.startDragInlet(0, "in1")


        def complete_qdrag_exec():
            QTest.mouseMove(self.view)
            QTest.qWait(50)
            QTest.mouseClick(self.view, Qt.MouseButton.LeftButton)

        QTimer.singleShot(1000, complete_qdrag_exec)
        QTest.mousePress(drag_source, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))
        QTest.mouseMove(drag_source, QPoint(50, 50))  # Ensure distance sufficient for DND start threshold

        QTest.mouse(self.view, 
            Qt.MouseButton.LeftButton, 
            pos=inlet.pos().toPoint()+QPoint(2,2)
        )


    def test_dragging_inlet_to_outlet(self):
        ...


class TestInvalidInletDrags(unittest.TestCase):
    def test_dragging_inlet_to_inlet(self):
        ...


class TestValidOutletDrags(unittest.TestCase):
    def test_dragging_outlet_to_empty(self):
        ...

    def test_dragging_outlet_to_inlet(self):
        ...


class TestValidEdgeDrags(unittest.TestCase):
    def test_dragging_edge_source_to_empty(self):
        ...

    def test_dragging_edge_source_to_inlet(self):
        ...

    def test_dragging_edge_source_back(self):
        ...

    def test_dragging_edge_target_to_empty(self):
        ...

    def test_dragging_edge_target_to_inlet(self):
        ...

    def test_dragging_edge_target_back(self):
        ...

    

if __name__ == "__main__":
    unittest.main()