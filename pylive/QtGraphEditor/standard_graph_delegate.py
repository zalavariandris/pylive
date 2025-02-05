from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.NetworkXGraphEditor.nx_graph_shapes import (
    ArrowLinkShape, RoundedLinkShape,
    BaseNodeItem,
    BaseLinkItem, 
    PortShape, distribute_items_horizontal
)

from pylive.NetworkXGraphEditor.nx_network_model import (
    NXNetworkModel,
    _NodeId, _EdgeId
)
from pylive.QtGraphEditor.nodes_model import UniqueFunctionItem
from pylive.QtGraphEditor.fields_model import FieldItem
from pylive.QtGraphEditor.widgets.standard_node_widget import StandardNodeWidget
from pylive.QtGraphEditor.widgets.standard_port_widget import StandardPortWidget



class StandardGraphDelegate(QObject):
    """Any QGraphicsItem can be used as a node or an edge graphics
    the delegate must emit a nodePositionchanged Signal, when a node position changed
    updateLinkPosition will be called when a linked node position changed"""

    ### NODE DELEGATE
    nodePositionChanged = Signal(QGraphicsItem)
    def createNodeEditor(self, parent:'QGraphEditorScene', index:QModelIndex|QPersistentModelIndex)->BaseNodeItem:
        node_widget = StandardNodeWidget()
        node_widget.setHeading(f"{index.data(Qt.ItemDataRole.DisplayRole)}")
        node_widget.scenePositionChanged.connect(lambda node=node_widget: self.nodePositionChanged.emit(node))
        parent.addItem(node_widget)
        return node_widget

    def createInletEditor(self, parent:QGraphicsItem, node_index:QModelIndex|QPersistentModelIndex, inlet:object)->QGraphicsWidget:
        port_editor = StandardPortWidget(f"{inlet}", parent)
        parent = cast(StandardNodeWidget, parent)
        parent.insertInlet(0, port_editor)
        # item.pressed.connect(lambda name=name: self.inletPressed.emit(name))
        return port_editor

    def createOutletEditor(self, parent:QGraphicsItem, node_index:QModelIndex|QPersistentModelIndex, outlet:object)->QGraphicsWidget:
        port_editor = StandardPortWidget(f"{outlet}", parent)
        port_editor._nameitem.setPos(-24,0)
        parent = cast(StandardNodeWidget, parent)
        parent.insertOutlet(0, port_editor)

        def on_press(node_index=node_index, port_editor=port_editor):
            scene = cast('QGraphEditorScene', port_editor.scene())
            scene.startDragOutlet(node_index.row())
            
        port_editor.pressed.connect(on_press)
        return port_editor

    def updateNodeEditor(self, index:QModelIndex|QPersistentModelIndex, editor:QGraphicsItem)->None:
        editor = cast(StandardNodeWidget, editor)
        editor.setHeading( index.data(Qt.ItemDataRole.DisplayRole) )

    ### EDGE DELEGATE
    def createEdgeEditor(self, edge_idx:QModelIndex|QPersistentModelIndex)->BaseLinkItem:
        label = edge_idx.data(Qt.ItemDataRole.DisplayRole)
        link = RoundedLinkShape(label if label else "", orientation=Qt.Orientation.Horizontal)
        link.setZValue(-1)
        return link

    def updateEdgeEditor(self, edge_idx:QModelIndex|QPersistentModelIndex, editor:QGraphicsItem)->None:
        ...

    def updateLinkPosition(self, 
        edge_editor, 
        source:QGraphicsItem|QPointF, 
        target:QGraphicsItem|QPointF
    ):
        edge_editor.move(source, target)

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


