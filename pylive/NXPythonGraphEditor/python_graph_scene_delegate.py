from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from numpy import isin

from pylive.NetworkXGraphEditor.nx_graph_shapes import BaseNodeItem
from pylive.NetworkXGraphEditor.nx_network_model import NXNetworkModel, _NodeId

from pylive.NetworkXGraphEditor.nx_network_scene_outlet_to_inlet import NXNetworkSceneDelegate
from pylive.NetworkXGraphEditor.nx_network_scene_delegate import NXNetworkSceneDelegate, StandardNodeItem
from pylive.NetworkXGraphEditor.nx_graph_shapes import (
    ArrowLinkShape, RoundedLinkShape,
    BaseNodeItem,
    BaseLinkItem, 
    PortShape
)


from python_graph_model import PythonGraphModel


class PythonFunctionNode(BaseNodeItem):
    def __init__(self, name:str, label:str, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        name_item = QGraphicsTextItem(name)
        name_item.adjustSize()
        name_item.setPos(0,-2)
        name_item.setParentItem(self)
        name_item.adjustSize()
        self.setGeometry(QRectF(0,0, name_item.textWidth(),20))
        label_item = QGraphicsTextItem()
        label_item.setHtml("<em>"+label+"</em>")
        label_item.adjustSize()
        label_item.setPos(self.geometry().width(),-2)
        label_item.setParentItem(self)
        label_item.adjustSize()


    # def sizeHint(self, which, constraint=QSizeF()) -> QSizeF:
    #     return QSizeF(40, 40)

    def paint(self, painter, option, widget=None):
        pen = painter.pen()
        pen.setBrush(self.palette().text())
        if self.isSelected():
            pen.setBrush(self.palette().accent())
        painter.setPen(pen)

        rect = QRectF(QPoint(0,0), self.geometry().size())
        painter.drawRoundedRect(rect, 6,6)


class PythonSubgraphNode(BaseNodeItem):
    def __init__(self, name:str, label:str, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        name_item = QGraphicsTextItem()
        name_item.setPlainText("subgraph\n"+name)

        name_item.adjustSize()
        name_item.setPos(0,-2)
        name_item.setParentItem(self)
        name_item.adjustSize()
        self.setGeometry(QRectF(0,0, name_item.textWidth(), 70))

        label_item = QGraphicsTextItem()
        label_item.setHtml(f"<em>"+label+"</em>")
        label_item.adjustSize()
        label_item.setPos(self.geometry().width(),-2)
        label_item.setParentItem(self)
        label_item.adjustSize()

        
    # def sizeHint(self, which, constraint=QSizeF()) -> QSizeF:
    #     return QSizeF(40, 40)

    def paint(self, painter, option, widget=None):
        pen = painter.pen()
        pen.setBrush(self.palette().text())
        if self.isSelected():
            pen.setBrush(self.palette().accent())
        painter.setPen(pen)

        rect = QRectF(QPoint(0,0), self.geometry().size())
        painter.drawRoundedRect(rect, 6,6)


class PythonGraphDelegate(NXNetworkSceneDelegate):
    @override
    def createNodeEditor(self, model, node_id: _NodeId) -> 'BaseNodeItem':
        fn = model.function(node_id)
        if isinstance(fn, PythonGraphModel):
            return PythonSubgraphNode(fn.__class__.__name__, f"{node_id}")
        else:
            fn = model.function(node_id)
            try:
                name_text = fn.__name__
            except AttributeError:
                try:
                    name_text = fn.__class__.__name__
                except AttributeError:
                    name_text = str(fn)
            widget = PythonFunctionNode(name_text, f"{node_id}")
            return widget

    @override
    def updateNodeEditor(self, model, node_id: _NodeId, editor:'BaseNodeItem', attributes:list[str])->None:
        node_editor = cast(PythonFunctionNode, editor)

    @override
    def createLinkEditor(self, model,
        u:_NodeId|None, v:_NodeId|None, k:tuple[str|None, str|None],
        )->BaseLinkItem:

        assert isinstance(k, tuple)
        link = RoundedLinkShape("")  #(f"{k[1]}" if k[1] else "")
        link.setZValue(-1)
        return link

    @override
    def createAttributeEditor(self, parent_node: QGraphicsItem, model: NXNetworkModel, node_id: _NodeId, attr: str)->QGraphicsItem|None:
        return None

    def updateAttributeEditor(self, model: NXNetworkModel, node_id:Hashable, attr:str, editor: QGraphicsItem)->None:
        return None

    # def setNodePropertyModel(self, model:NXNetworkModel, node_id:Hashable, prop:str, editor: QGraphicsItem):
    #     ...
