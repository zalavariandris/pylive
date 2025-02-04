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



class QGraphEditorDelegate(QObject):
    """Any QGraphicsItem can be used as a node or an edge graphics
    the delegate must emit a nodePositionchanged Signal, when a node position changed
    updateLinkPosition will be called when a linked node position changed"""

    ### NODE DELEGATE
    nodePositionChanged = Signal(QGraphicsItem)
    def createNodeEditor(self, parent:'QGraphEditorScene', index:QModelIndex|QPersistentModelIndex)->BaseNodeItem:
        node_widget = StandardNodeWidget()
        node_widget.setHeading(f"{index.data(Qt.ItemDataRole.DisplayRole)}")
        node_widget.scenePositionChanged.connect(lambda node=node_widget: self.nodePositionChanged.emit(node))
        
        # node_data_item = cast(UniqueFunctionItem, index.internalPointer())
        # for idx, inlet in enumerate(node_data_item.inlets()):
        #     node_widget.insertInlet(idx, inlet)
        
            
        # node_widget.insertOutlet(0, "out")

        # node_widget.pressed.connect(lambda: parent.startDrag())

        # node_widget.installEventFilter(self)

        # for port, _ in node_widget._inlets:
        #     port.setAcceptDrops(True)
        #     port.installEventFilter(self)
        
        # def initiate_connection(graph_scene, node_index,  outlet_name):
        #     if graph_scene.views():
        #         return

        #     scene_view = graph_scene.views()[0]
        #     drag = QDrag(scene_view)
        #     drag.e
        #     # mimeData = QMimeData()

        #     # mimeDatamsetText(outlet_name);
        #     # drag->setMimeData(mimeData);
        #     # # graph_scene.initiateConnection(node_index, outlet_name)

        # node_widget.outletPressed.connect(lambda name, scene=parent, index=index: 
        #     initiate_connection(scene, index, name) )
            
        return node_widget

    # def nodeEditorEvent(self, event:QEvent, model:QAbstractItemModel, option:QStyleOptionViewItem, index:QModelIndex)->bool:
    #     return False

    # def eventFilter(self, watched: QObject, event: QEvent) -> bool:
    #     if event.type() == QEvent.Type.GraphicsSceneMousePress:
    #         print("event filter")
    #         event = cast(QGraphicsSceneMouseEvent, event)
    #         drag = QDrag(event.widget())
    #         mime = QMimeData()
    #         drag.setMimeData(mime)
    #         app = QApplication.instance()
    #         app.installEventFilter(drag)
    #         drag.exec()
    #         app.removeEventFilter(drag)
    #         return True

    #     elif event.type() == QEvent.Type.GraphicsSceneMouseMove:
    #         print("move move")

    #     elif event.type() == QEvent.Type.GraphicsSceneDragEnter:
    #         print("drag enter")
    #         return True

    #     return super().eventFilter(watched, event)

    def updateNodeEditor(self, index:QModelIndex|QPersistentModelIndex, editor:'BaseNodeItem')->None:
        editor = cast(StandardNodeWidget, editor)
        editor.setHeading( index.data(Qt.ItemDataRole.DisplayRole) )

    ### EDGE DELEGATE
    def createEdgeEditor(self, edge_idx:QModelIndex|QPersistentModelIndex)->BaseLinkItem:
        link = RoundedLinkShape(f"{edge_idx.data(Qt.ItemDataRole.EditRole)}", orientation=Qt.Orientation.Horizontal)
        link.setZValue(-1)
        return link

    def updateEdgeEditor(self, edge_idx:QModelIndex|QPersistentModelIndex, editor:'BaseLinkItem')->None:
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


