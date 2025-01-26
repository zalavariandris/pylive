from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.NetworkXGraphEditor.nx_graph_shapes import (
    ArrowLinkShape, RoundedLinkShape,
    BaseNodeItem,
    BaseLinkItem, 
    PortShape
)

from pylive.NetworkXGraphEditor.nx_network_model import (
    NXNetworkModel,
    _NodeId, _EdgeId
)

class StandardNodeItem(BaseNodeItem):
    def __init__(self, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

    def paint(self, painter, option, widget=None):
        rect = self.geometry()

        pen = painter.pen()
        pen.setBrush(self.palette().text())
        if self.isSelected():
            pen.setBrush(self.palette().accent())
        painter.setPen(pen)

        rect.moveTo(QPoint(0,0))
        painter.drawRoundedRect(rect, 6,6)


class QGraphEditorDelegate(QObject):
    """Any QGraphicsItem can be used as a node or an edge graphics
    the delegate must emit a nodePositionchanged Signal, when a node position changed
    updateLinkPosition will be called when a linked node position changed"""

    nodePositionChanged = Signal(QGraphicsItem)
    def createNodeEditor(self, node_idx:QModelIndex|QPersistentModelIndex)->BaseNodeItem:
        node = StandardNodeItem()
        node.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        node.scenePositionChanged.connect(lambda node=node: self.nodePositionChanged.emit(node))
        labelitem = QGraphicsTextItem(f"{node_idx.data(Qt.ItemDataRole.DisplayRole)}")
        labelitem.adjustSize()
        labelitem.setPos(0,-2)
        labelitem.setParentItem(node)

        node.setGeometry(QRectF(0, 0, labelitem.textWidth(),20))
        return node

    def updateNodeEditor(self, node_idx:QModelIndex|QPersistentModelIndex, editor:'BaseNodeItem')->None:
        ...

    def createEdgeEditor(self, edge_idx:QModelIndex|QPersistentModelIndex)->BaseLinkItem:
        link = RoundedLinkShape(f"{edge_idx.data(Qt.ItemDataRole.DisplayRole)}", orientation=Qt.Orientation.Horizontal)
        link.setZValue(-1)
        return link

    def updateEdgeEditor(self, edge_idx:QModelIndex|QPersistentModelIndex, editor:'BaseLinkItem')->None:
        ...

    def updateLinkPosition(self, edge_editor, source_node_editor, target_node_editor):
        edge_editor.move(source_node_editor, target_node_editor)

    # def createInletEditor(self, parent_node:QGraphicsItem, node_id:_NodeId, key:str)->QGraphicsItem:
    #     assert isinstance(key, str)
    #     inlet = PortShape(f"{key}")
        
    #     inlet.setParentItem(parent_node)
    #     return inlet

    # def createOutletEditor(self, parent_node:QGraphicsItem, node_id:_NodeId, key:str)->QGraphicsItem:
    #     assert isinstance(key, str)
    #     outlet = PortShape(f"{key}")
    #     outlet.setParentItem(parent_node)
    #     return outlet

    # def createAttributeEditor(self, parent_node: QGraphicsItem, model: NXNetworkModel, node_id: _NodeId, attr: str)->QGraphicsItem|None:
    #     if isinstance(attr, str) and attr.startswith("_"):
    #         return None
    #     value = model.getNodeAttribute(node_id, attr)
    #     badge = QGraphicsTextItem(f"{attr}:, {value}")
    #     badge.setParentItem(parent_node)
    #     badge.setPos(
    #         parent_node.boundingRect().right(),
    #         (parent_node.boundingRect()|parent_node.childrenBoundingRect()).bottom()
    #     )
    #     return badge

    # def updateAttributeEditor(self, model: NXNetworkModel, node_id:Hashable, attr:str, editor: QGraphicsItem):
    #     value = model.getNodeAttribute(node_id, attr)
    #     editor = cast(QGraphicsTextItem, editor)
    #     editor.setPlainText(f"{attr}: {value}")

