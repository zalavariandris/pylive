from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.VisualCode_NetworkX.UI.nx_graph_shapes import RoundedLinkShape


from pylive.VisualCode_v4.graph_editor.standard_node_widget import StandardNodeWidget
from pylive.VisualCode_v4.graph_editor.standard_port_widget import StandardPortWidget
from pylive.VisualCode_v4.graph_editor.standard_link_widget import RoundedLinkWidget



class StandardGraphDelegate(QObject):
    """Any QGraphicsItem can be used as a node or an edge graphics
    the delegate must emit a nodePositionchanged Signal, when a node position changed
    updateLinkPosition will be called when a linked node position changed"""

    ### NODE DELEGATE
    nodePositionChanged = Signal(QGraphicsItem)
    def createNodeWidget(self, parent:QGraphicsScene, index:QModelIndex)->QGraphicsItem:
        node_widget = StandardNodeWidget()
        node_widget.setHeading(f"{index.data(Qt.ItemDataRole.DisplayRole)}")
        node_widget.scenePositionChanged.connect(lambda node=node_widget: self.nodePositionChanged.emit(node))
        parent.addItem(node_widget)
        return node_widget

    def createInletWidget(self, parent:QGraphicsItem, node_index:QModelIndex, inlet:str, idx:int=-1)->QGraphicsItem:
        port_editor = StandardPortWidget(f"{inlet}")
        port_editor._nameitem.setPos(2,-24)
        return port_editor

    def createOutletWidget(self, parent:QGraphicsItem, node_index:QModelIndex, outlet:str, idx:int=-1)->QGraphicsItem:
        port_editor = StandardPortWidget(f"{outlet}", parent)
        port_editor._nameitem.setPos(-24,0)
        # parent = cast(StandardNodeWidget, parent)
        # if idx<0:
        #     idx = len(parent._outlets)
        # parent.insertOutlet(idx, port_editor)
        return port_editor

    def updateNodeWidget(self, index:QModelIndex, node_widget:QGraphicsItem)->None:
        node_widget = cast(StandardNodeWidget, node_widget)
        node_widget.setHeading( index.data(Qt.ItemDataRole.DisplayRole) )

    ### EDGE DELEGATE
    def createEdgeWidget(self, edge_idx:QModelIndex)->QGraphicsItem:
        # app = QApplication.instance()
        # assert isinstance(app, QGuiApplication)
        # link = QGraphicsPathItem()
        # link.setPen(QPen(app.palette().text(), 1))
        link = RoundedLinkWidget()
        link.setZValue(-1)
        return link
        # label = edge_idx.data(Qt.ItemDataRole.DisplayRole)
        # link = RoundedLinkShape(label if label else "", orientation=Qt.Orientation.Vertical)
        # link.setZValue(-1)
        # return link

    def updateEdgeWidget(self, edge_idx:QModelIndex, editor:QGraphicsItem)->None:
        ...

    def updateEdgePosition(self, 
        edge_editor: QGraphicsItem, 
        source:QGraphicsItem|QPointF, 
        target:QGraphicsItem|QPointF
    ):
        # assert isinstance(edge_editor, QGraphicsLineItem)
        line = QLineF()

        match source:
            case QGraphicsItem():
                line.setP1(source.scenePos())
            case QPointF():
                line.setP1(source)
            case _:
                raise ValueError()

        match target:
            case QGraphicsItem():
                line.setP2(target.scenePos())
            case QPointF():
                line.setP2(target)
            case _:
                raise ValueError(f"target is not a widget or a point, got{target}")

        # edge_editor = cast(QGraphicsPathItem, edge_editor)
        # from pylive.utils.geo import makeHorizontalRoundedPath, makeVerticalRoundedPath
        # edge_editor.setPath( makeVerticalRoundedPath(line) )

        # edge_editor = cast(QGraphicsLineItem, edge_editor)
        # edge_editor.setLine(line)
        edge_widget = cast(RoundedLinkWidget, edge_editor)
        edge_widget.move(source, target)


