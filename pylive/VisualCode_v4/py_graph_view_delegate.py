from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.VisualCode_v4.graph_editor.standard_graph_delegate import StandardGraphDelegate
from pylive.VisualCode_v4.py_node_widget import PyNodeWidget

class PyGraphViewDelegate(StandardGraphDelegate):
    def createNodeWidget(self, parent:QGraphicsScene, index:QModelIndex)->QGraphicsItem:
        node_widget = PyNodeWidget()
        node_widget.setHeading(f"{index.data(Qt.ItemDataRole.DisplayRole)}")
        node_widget.scenePositionChanged.connect(lambda node=node_widget: self.nodePositionChanged.emit(node))
        parent.addItem(node_widget)
        return node_widget

    def updateNodeWidget(self, index:QModelIndex, node_widget:QGraphicsItem)->None:
        node_widget = cast(PyNodeWidget, node_widget)
        node_widget.setHeading( index.data(Qt.ItemDataRole.DisplayRole) )
        index.data(Qt.ItemDataRole.ForegroundRole)