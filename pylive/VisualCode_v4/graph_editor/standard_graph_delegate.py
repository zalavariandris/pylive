from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.VisualCode_NetworkX.UI.nx_graph_shapes import RoundedLinkShape


from pylive.VisualCode_v4.graph_editor.standard_node_widget import StandardNodeWidget
from pylive.VisualCode_v4.graph_editor.standard_port_widget import StandardPortWidget
from pylive.VisualCode_v4.graph_editor.standard_link_widget import StandardLinkPath, RoundedLinkPath
from pylive.utils.geo import makeLineBetweenShapes



class StandardGraphDelegate(QObject):
    """Any QGraphicsItem can be used as a node or an edge graphics
    the delegate must emit a nodePositionchanged Signal, when a node position changed
    updateLinkPosition will be called when a linked node position changed"""

    nodePositionChanged = Signal(QGraphicsItem)
    ### NODE DELEGATE
    def createNodeWidget(self, parent:QGraphicsScene, index:QModelIndex)->QGraphicsItem:
        node_widget = StandardNodeWidget()
        node_widget.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        node_widget.setHeading(f"{index.data(Qt.ItemDataRole.DisplayRole)}")
        node_widget.scenePositionChanged.connect(lambda node=node_widget: self.nodePositionChanged.emit(node))
        parent.addItem(node_widget)
        return node_widget

    def updateNodeWidget(self, index:QModelIndex, node_widget:QGraphicsItem)->None:
        node_widget = cast(StandardNodeWidget, node_widget)
        node_widget.setHeading( index.data(Qt.ItemDataRole.DisplayRole) )

    def createInletWidget(self, parent:QGraphicsItem, node_index:QModelIndex, inlet:str, idx:int=-1)->QGraphicsItem:
        port_editor = StandardPortWidget(f"{inlet}")
        port_editor._nameitem.setPos(2,-24)
        return port_editor

    def createOutletWidget(self, parent:QGraphicsItem, node_index:QModelIndex, outlet:str, idx:int=-1)->QGraphicsItem:
        port_editor = StandardPortWidget(f"{outlet}", parent)
        port_editor._nameitem.setPos(-24,0)
        # parent = cast(StandardNodeWidget, parent)
        # if idx<0:`
        #     idx = len(parent._outlets)
        # parent.insertOutlet(idx, port_editor)
        return port_editor

    ### EDGE DELEGATE
    def createEdgeWidget(self, edge_idx:QModelIndex)->QGraphicsLineItem:
        # app = QApplication.instance()
        # assert isinstance(app, QGuiApplication)
        # link = QGraphicsPathItem()
        # link.setPen(QPen(app.palette().text(), 1))
        link = StandardLinkPath()
        link.setZValue(-1)
        link.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        return link
        # label = edge_idx.data(Qt.ItemDataRole.DisplayRole)
        # link = RoundedLinkShape(label if label else "", orientation=Qt.Orientation.Vertical)
        # link.setZValue(-1)
        # return link

    def updateEdgeWidget(self, edge_idx:QModelIndex, editor:QGraphicsItem)->None:
        ...

    def updateEdgePosition(self, 
        edge_widget: QGraphicsLineItem, 
        source:QGraphicsItem|QPointF, 
        target:QGraphicsItem|QPointF
    ):
        # assert isinstance(edge_editor, QGraphicsLineItem)
        line = makeLineBetweenShapes(source, target)
        edge_widget.setLine(line)


