from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

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


class PythonFunctionNodeView(BaseNodeItem):
    def __init__(self, model:PythonGraphModel, node_id, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        fn = model.function(node_id)
        fn_item = QGraphicsTextItem()
        fn_item.setHtml(f"<strong>{fn.__name__}</strong>")
        fn_item.adjustSize()
        fn_item.setPos(0,-2)
        fn_item.setParentItem(self)
        fn_item.adjustSize()
        self.setGeometry(QRectF(0,0, fn_item.textWidth(),20))
        name_item = QGraphicsTextItem()
        name_item.setHtml(f"<em>{node_id}</em>")
        name_item.adjustSize()
        name_item.setPos(self.geometry().width(),-2)
        name_item.setParentItem(self)
        name_item.adjustSize()

        badge_label = QGraphicsTextItem()
        badge_label.setHtml(f"")
        badge_label.adjustSize()
        badge_label.setPos(self.geometry().width(), name_item.boundingRect().bottom())
        badge_label.setParentItem(self)
        badge_label.adjustSize()
        self.badge_label = badge_label

        self._node_id = node_id
        self._model = model
        
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

    def onAttributesChanged(self, change:list[str]):
        if 'cache' in change:
            cached = self._model.getNodeAttribute(self._node_id, 'cache')
            print(self._node_id, "cached", cached)
            if cached:
                self.badge_label.setPlainText("cached")
                self.badge_label.adjustSize()
            else:
                self.badge_label.setPlainText("")


class NXGraphFactoryDelegate():
    def __init__(self, 
        nodeFactory=lambda model, node_id: PythonFunctionNodeView(model, node_id), 
        edgeFactory=lambda model, edge_id: RoundedLinkShape(model, edge_id),
        # inletFactory: None,
        # outletfactory: None,
        attributeFactory=lambda model, node_id, attr: QGraphicsTextItem(f"{attr}"),
        attributeUpdate=lambda model, node_id, attr, editor: editor.onAttributesChanged(node_id, attr),
        nodeUpdate=lambda editor, node_id, attributes: editor.onAttributesChanged(node_id, attributes),
        # edgeUpdate=lambda editor, edge_id, attributes: editor.onAttributesChanged(edge_id, attributes),
    ):
        ...


class PythonGraphDelegate(NXNetworkSceneDelegate):
    def __init__(self, 
        nodeFactory: Callable[[PythonGraphModel, Hashable], QGraphicsItem],
        edgeFactory=lambda model, edge_id: RoundedLinkShape(model, edge_id),
        # inletFactory: None,
        # outletfactory: None,
        attributeFactory=lambda model, node_id, attr: QGraphicsTextItem(f"{attr}"),
        attributeUpdate=lambda model, node_id, attr, editor: editor.onAttributesChanged(node_id, attr),
        nodeUpdate=lambda editor, node_id, attributes: editor.onAttributesChanged(node_id, attributes),
        # edgeUpdate=lambda editor, edge_id, attributes: editor.onAttributesChanged(edge_id, attributes),
    ):
        ...
    # @override
    # def createNodeEditor(self, model, node_id: _NodeId) -> 'BaseNodeItem':
    #     return PythonFunctionNodeView(model, node_id)

    # @override
    # def updateNodeEditor(self, model, node_id: _NodeId, editor:'BaseNodeItem', attributes:list[str])->None:
    #     cast(PythonFunctionNodeView, editor).onAttributesChanged(attributes)

    # @override
    # def createLinkEditor(self, model,
    #     u:_NodeId|None, v:_NodeId|None, k:tuple[str|None, str|None],
    #     )->BaseLinkItem:

    #     assert isinstance(k, tuple)
    #     link = RoundedLinkShape("")  #(f"{k[1]}" if k[1] else "")
    #     link.setZValue(-1)
    #     return link

    # @override
    # def createAttributeEditor(self, parent_node: QGraphicsItem, model: NXNetworkModel, node_id: _NodeId, attr: str)->QGraphicsItem|None:
    #     return None

    # def updateAttributeEditor(self, model: NXNetworkModel, node_id:Hashable, attr:str, editor: QGraphicsItem)->None:
    #     return None

    # # def setNodePropertyModel(self, model:NXNetworkModel, node_id:Hashable, prop:str, editor: QGraphicsItem):
    # #     ...

PythonGraphDelegate(
    nodeFactory=PythonFunctionNodeView,
    edgeFactory=RoundedLinkShape,
    # inletFactory: None,
    # outletfactory: None,
    attributeFactory=lambda model, node_id, attr: QGraphicsTextItem(f"{attr}"),
    attributeUpdate=lambda model, node_id, attr, editor: editor.onAttributesChanged(node_id, attr),
    nodeUpdate=lambda editor, node_id, attributes: editor.onAttributesChanged(node_id, attributes),
)
