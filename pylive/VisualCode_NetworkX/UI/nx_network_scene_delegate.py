from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.VisualCode_NetworkX.UI.nx_graph_shapes import (
    ArrowLinkShape, RoundedLinkShape,
    BaseNodeItem,
    BaseLinkItem, 
    PortShape
)

from pylive.VisualCode_NetworkX.UI.nx_network_model import (
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


class NXNetworkSceneDelegate:
    def createNodeEditor(self, model, node_id:_NodeId)->BaseNodeItem:
        node = StandardNodeItem()
        
        labelitem = QGraphicsTextItem(f"{node_id}")
        labelitem.adjustSize()
        labelitem.setPos(0,-2)
        labelitem.setParentItem(node)

        node.setGeometry(QRectF(0,0,labelitem.textWidth(),20))
        return node

    def updateNodeEditor(self, model, node_id: _NodeId, editor:'BaseNodeItem', attributes:list[str])->None:
        ...


    def createLinkEditor(self, model,
        u:_NodeId|None, v:_NodeId|None, k:tuple[str|None, str|None],
        )->BaseLinkItem:

        assert isinstance(k, tuple)
        link = ArrowLinkShape(f"{k[1]}" if k[1] else "")
        link.setZValue(-1)
        return link

    def createInletEditor(self, parent_node:QGraphicsItem, node_id:_NodeId, key:str)->QGraphicsItem:
        assert isinstance(key, str)
        inlet = PortShape(f"{key}")
        
        inlet.setParentItem(parent_node)
        return inlet

    def createOutletEditor(self, parent_node:QGraphicsItem, node_id:_NodeId, key:str)->QGraphicsItem:
        assert isinstance(key, str)
        outlet = PortShape(f"{key}")
        outlet.setParentItem(parent_node)
        return outlet

    def createAttributeEditor(self, parent_node: QGraphicsItem, model: NXNetworkModel, node_id: _NodeId, attr: str)->QGraphicsItem|None:
        if isinstance(attr, str) and attr.startswith("_"):
            return None
        value = model.getNodeAttribute(node_id, attr)
        badge = QGraphicsTextItem(f"{attr}:, {value}")
        badge.setParentItem(parent_node)
        badge.setPos(
            parent_node.boundingRect().right(),
            (parent_node.boundingRect()|parent_node.childrenBoundingRect()).bottom()
        )
        return badge

    def updateAttributeEditor(self, model: NXNetworkModel, node_id:Hashable, attr:str, editor: QGraphicsItem):
        value = model.getNodeAttribute(node_id, attr)
        editor = cast(QGraphicsTextItem, editor)
        editor.setPlainText(f"{attr}: {value}")

