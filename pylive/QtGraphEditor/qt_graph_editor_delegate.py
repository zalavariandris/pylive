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
from pylive.QtGraphEditor.standard_node_item import StandardNodeItem



# class GraphLinkTool(QObject):
#     def __init__(self, graphscene:'QGraphEditorScene'):
#         super().__init__(parent=graphscene)
#         import typing
#         self._graphscene = graphscene
#         self.loop = QEventLoop()
#         self.draft:BaseLinkItem|None = None
#         self.direction:Literal['forward', 'backward'] = 'forward'

#     def graphscene(self)->'NXNetworkScene':
#         return self._graphscene

#     def startFromOutlet(self, node_id:_NodeId, key:str):
#         model = self.graphscene().model()
#         link = self.graphscene().delegate.createLinkEditor(model, node_id, None, (key, None))
#         self.draft = link
#         assert self.draft
#         self.draft.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
#         self.draft.setAcceptHoverEvents(False)
#         self.draft.setEnabled(False)
#         self.draft.setActive(False)
#         self.graphscene().addItem(self.draft)

#         self.source_node_id = node_id
#         self.source_key = key

#         ### start event loop
#         app = QApplication.instance()
#         assert isinstance(app, QGuiApplication)
#         self.direction = 'forward'
#         app.installEventFilter(self)
#         self.loop.exec()
#         app.removeEventFilter(self)

#     def startFromInlet(self, node_id:_NodeId, key:str):
#         model = self.graphscene().model()
#         self.draft = self.graphscene().delegate.createLinkEditor(model, None, node_id, (None, key))
#         assert self.draft
#         self.graphscene().addItem(self.draft)
        
#         self.source_node_id = node_id
#         self.source_key = key

#         ### start event loop
#         app = QApplication.instance()
#         assert isinstance(app, QGuiApplication)
#         self.direction = 'backward'
#         app.installEventFilter(self)
#         self.loop.exec()
#         app.removeEventFilter(self)

#     def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
#         ...

#     def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
#         assert self.draft is not None
#         match self.direction:
#             case 'forward':
#                 assert self.source_node_id is not None
#                 if target := self.graphscene().inletAt(event.scenePos()):
#                     target_node_id, target_key = target
#                     self.draft.move(
#                         self.graphscene().outletGraphicsObject(self.source_node_id, self.source_key),
#                         self.graphscene().inletGraphicsObject(target_node_id, target_key)
#                     )
#                 else:
#                     self.draft.move(
#                         self.graphscene().outletGraphicsObject(self.source_node_id, self.source_key), 
#                         event.scenePos()
#                     )

#             case 'backward':
#                 assert self.source_node_id is not None
#                 if target := self.graphscene().outletAt(event.scenePos()):
#                     target_node_id, target_key = target
#                     self.draft.move(
#                         self.graphscene().outletGraphicsObject(target_node_id, target_key),
#                         self.graphscene().inletGraphicsObject(self.source_node_id, self.source_key)
#                     )
#                 else:
#                     self.draft.move(
#                         event.scenePos(),
#                         self.graphscene().inletGraphicsObject(self.source_node_id, self.source_key)
#                     )

#     def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
#         assert self.draft is not None
#         scene = self.graphscene()
#         self.graphscene().removeItem(self.draft)
#         model = scene.model()
#         assert model is not None
#         match self.direction:
#             case 'forward':
#                 assert self.source_node_id is not None
#                 if inlet_id := self.graphscene().inletAt(event.scenePos()):
#                     inlet_node_id, inlet_key = inlet_id
#                     model.addEdge(self.source_node_id, inlet_node_id, (self.source_key, inlet_key))
#                 else:
#                     pass

#             case 'backward':
#                 assert self.source_node_id is not None
#                 if outlet_id := self.graphscene().outletAt(event.scenePos()):
#                     outlet_node_id, outlet_key = outlet_id
#                     edge_id:_EdgeId = outlet_node_id, self.source_node_id, (outlet_key, self.source_key)
#                     model.addEdge(*edge_id)
#                 else:
#                     pass

        
#         self.loop.exit()

#     def eventFilter(self, watched: QObject, event: QEvent) -> bool:
#         match event.type():
#             case QEvent.Type.GraphicsSceneMouseMove:
#                 self.mouseMoveEvent(cast(QGraphicsSceneMouseEvent, event))
#                 return True
#             case QEvent.Type.GraphicsSceneMouseRelease:
#                 self.mouseReleaseEvent(cast(QGraphicsSceneMouseEvent, event))
#                 return True
#             case _:
#                 pass
#         return super().eventFilter(watched, event)


class QGraphEditorDelegate(QObject):
    """Any QGraphicsItem can be used as a node or an edge graphics
    the delegate must emit a nodePositionchanged Signal, when a node position changed
    updateLinkPosition will be called when a linked node position changed"""

    ### NODE DELEGATE
    nodePositionChanged = Signal(QGraphicsItem)
    def createNodeEditor(self, parent:'QGraphEditorScene', index:QModelIndex|QPersistentModelIndex)->BaseNodeItem:
        node_widget = StandardNodeItem()
        node_widget.setHeading(f"{index.data(Qt.ItemDataRole.DisplayRole)}")
        node_widget.scenePositionChanged.connect(lambda node=node_widget: self.nodePositionChanged.emit(node))
        node_data_item = cast(UniqueFunctionItem, index.internalPointer())

        for idx, inlet in enumerate(node_data_item.inlets()):
            node_widget.insertInlet(idx, inlet)
            
        node_widget.insertOutlet(0, "out")

        node_widget.pressed.connect(lambda: parent.startEdge())

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
        editor = cast(StandardNodeItem, editor)
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


