#####################
# The Network Scene #
#####################

#
# A 'View' to represent a network of nodes, connected by inlets and outlets
#

# In QT ModelView terminology this is a 'View'.
# It is responsible to present (and potentially edit) the NXGraphModel
# GraphScene 'internaly' uses subclasses of GraphShapes that are also 'views'.
# these widgets are responsible to reference the graphscene,
# and the represented nodes, edge and ports.
#
# TODO: move the model editing capabilities
# from the widgets to a delegate, or the graphsene itself


from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from numpy import isin

from pylive.NetworkXGraphEditor.nx_graph_shapes import (
    ArrowLinkShape,
    BaseNodeItem,
    BaseLinkItem, RoundedLinkShape,
    PortShape,
    distribute_items_horizontal
)

##############
# GRAPHSCENE #
##############

from bidict import bidict
from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel
from pylive.NetworkXGraphEditor.nx_graph_selection_model import (
    NXGraphSelectionModel,
)

from dataclasses import dataclass

# define to NXGraphModel schema
type NodeId = Hashable
# type OutletId = tuple[Hashable, Hashable]
# type InletId = tuple[Hashable, Hashable]
# type LinkId = tuple[OutletId, InletId]





class NXNetworkScene(QGraphicsScene):
    def __init__(self, model: NXGraphModel, selection_model: NXGraphSelectionModel):
        super().__init__()

        self._model: NXGraphModel | None = None
        self._selection_model:NXGraphSelectionModel|None = None

        self.delegate = StandardGraphFactory()

        # configure QGraphicsScene
        # self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        # store model widget relations
        self._node_graphics_objects: bidict[NodeId, BaseNodeItem] = bidict()
        self._outlet_graphics_objects: bidict[tuple[NodeId, str], QGraphicsItem] = bidict()
        self._inlet_graphics_objects: bidict[tuple[NodeId, str], QGraphicsItem] = bidict()
        self._link_graphics_objects: bidict[tuple[NodeId, NodeId, tuple[str, str]], BaseLinkItem] = bidict()
        self._draft_link: BaseLinkItem | None = None

        # draft link: # TODO: consider moving it to the GraphView.
        # GraphView is supposed to be responsible for user interactions
        # self.draft: RoundedLinkShape | None = None  # todo use the widget itself?

        # set model
        # populate with initial model
        
        self.setModel(model)
        self.setSelectionModel(selection_model)

        self.selectionChanged.connect(self.selectionChangedEvent)

    def setSelectionModel(self, selection_model:NXGraphSelectionModel):
        if self._selection_model:
            self._selection_model.selectionChanged.disconnect(self.onSelectionChanged)

        if selection_model:
            selection_model.selectionChanged.connect(self.onSelectionChanged)

        # set selection model
        self._selection_model = selection_model

    def selectionChangedEvent(self):
        if not self._selection_model:
            return

        selected_nodes = [
            self._node_graphics_objects.inverse[node]
            for node in self.selectedItems()
            if node in self._node_graphics_objects.values()
        ]
        self._selection_model.setSelectedNodes(selected_nodes)

    def setModel(self, model: NXGraphModel):
        if self._model:
            model.nodesAdded.disconnect(self.onNodesCreated)
            model.nodesAboutToBeRemoved.disconnect(self.onNodesDeleted)
            model.edgesAdded.disconnect(self.onEdgesCreated)
            model.edgesAboutToBeRemoved.disconnect(self.onEdgesDeleted)

        if model:
            _ = model.nodesAdded.connect(self.onNodesCreated)
            _ = model.nodesAboutToBeRemoved.connect(self.onNodesDeleted)
            _ = model.edgesAdded.connect(self.onEdgesCreated)
            _ = model.edgesAboutToBeRemoved.connect(self.onEdgesDeleted)
        self._model = model

        ### populate graph
        self.onNodesCreated(self._model.nodes())
        edges:list[tuple[NodeId, NodeId, tuple[str, str]]] = [e for e in self._model.edges()]
        self.onEdgesCreated( edges )

        # layout items
        self.layout()

    def model(self):
        return self._model

    ### <<< Map the interactive graphics ids to widgets
    def nodeGraphicsObject(self, nodeId: NodeId) -> QGraphicsItem:
        return self._node_graphics_objects[nodeId]

    def outletGraphicsObject(self, node_id:NodeId, key:str) -> QGraphicsItem:
        assert isinstance(key, str)
        return self._outlet_graphics_objects[(node_id, key)]

    def inletGraphicsObject(self, node_id:NodeId, key: str) -> QGraphicsItem:
        assert isinstance(key, str)
        return self._inlet_graphics_objects[(node_id, key)]

    def linkGraphicsObject(self, u:NodeId, v:NodeId, k:tuple[str, str]) -> BaseLinkItem:
        return self._link_graphics_objects[(u, v, k)]

    def moveAttachedLinks(self, node_id:NodeId):
        from itertools import chain
        model = self.model()
        assert model
        for e in chain(model.inEdges(node_id), model.outEdges(node_id)):
            u, v, (o, i) = e
            outlet = self.outletGraphicsObject(u, o)
            inlet = self.inletGraphicsObject(v, i)
            link = self.linkGraphicsObject(u, v, (o, i))
            link.move(outlet, inlet)

    ### <<< Handle Model Signals
    def onNodesCreated(self, nodes: list[Hashable]):
        assert self._model
        for node_id in nodes:
            node = self.delegate.createNode(node_id)
            node.scenePositionChanged.connect(lambda node_id=node_id: self.moveAttachedLinks(node_id))
            self._node_graphics_objects[node_id] = node
            self.addItem(self.nodeGraphicsObject(node_id))

            if not self._model.hasNodeProperty(node_id, "inlets"):
                raise ValueError("Nodes must have an 'inlets' attribute")

            if not self._model.hasNodeProperty(node_id, "outlets"):
                raise ValueError("Nodes must have an 'outlets' attribute")

            inlets = []
            # inlet_names = 
            # assert isinstance(inlet_names, list), f" {inlet_names}"
            # assert all(
            #     isinstance(_, str) for _ in inlet_names
            # ), f"one of the inlet type currently not supported: {inlet_names}"

            for inlet_name in self._model.getNodeProperty(node_id, "inlets"):
                node = cast(BaseNodeItem, self.nodeGraphicsObject(node_id))
                inlet = self.delegate.createInlet(node, node_id, inlet_name)
                self._inlet_graphics_objects[(node_id, inlet_name)] = inlet
                inlets.append(inlet)
            # position inlet
            for inlet in inlets:
                inlet.setY(node.boundingRect().top()-3)
            distribute_items_horizontal(inlets, node.boundingRect())

            outlets = []
            outlet_names = self._model.getNodeProperty(node_id, "outlets")
            assert isinstance(outlet_names, list) and all(
                isinstance(_, str) for _ in outlet_names
            )
            for outlet_name in outlet_names:
                node = cast(BaseNodeItem, self.nodeGraphicsObject(node_id))
                outlet = self.delegate.createOutlet(node, node_id, outlet_name)
                self._outlet_graphics_objects[(node_id, outlet_name)] = outlet
                outlets.append(outlet)
            # position outlets
            for outlet in outlets:
                outlet.setY(node.boundingRect().bottom()+3)
            distribute_items_horizontal(outlets, node.boundingRect())


    def onEdgesDeleted(self, edges: Iterable[tuple[NodeId, NodeId, tuple[str, str]]]):
        for e in edges:
            u, v, (o, i) = e
            self.removeItem(self.linkGraphicsObject(u, v, (o, i)))
            if e in self._link_graphics_objects:
                del self._link_graphics_objects[e]

    def onEdgesCreated(self, edges: Iterable[tuple[NodeId, NodeId, tuple[str, str]]]):
        for e in edges:
            u, v, (o, i) = e
            link = self.delegate.createLink(u, v, (o, i))

            self._link_graphics_objects[e] = link
            self.addItem(link)

            u, v, (o, i) = e
            link.move(
                self.outletGraphicsObject(u, o),
                self.inletGraphicsObject(v, i)
            )

    def onNodesDeleted(self, nodes: list[NodeId]):
        for n in nodes:
            if n in self._node_graphics_objects:
                node_graphics_object = self.nodeGraphicsObject(n)
                raise NotImplementedError()

    def onModelReset(self):
        assert self._model
        ### clear graph
        self._node_graphics_objects.clear()
        self._inlet_graphics_objects.clear()
        self._link_graphics_objects.clear()
        self._node_graphics_objects.clear()
        self.clear()

        ### populate graph
        self.onNodesCreated(self._model.nodes())
        self.onEdgesCreated(self._model.edges())

        # layout items
        self.layout()

    def onSelectionChanged(self, selected: set[NodeId], deselected: set[NodeId]):
        if len(selected)>0 or len(deselected)>0:
            selected_widgets = [self.nodeGraphicsObject(n) for n in selected]
            deselected_widgets = [self.nodeGraphicsObject(n) for n in deselected]

            self.blockSignals(True)
            for widget in selected_widgets :
                widget.setSelected(True)

            for widget in deselected_widgets:
                widget.setSelected(False)
            self.blockSignals(False)

            self.selectionChanged.emit()

    ### <<< Handle Model Signals
    def nodeAt(self, position: QPointF) -> NodeId | None:
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                node_id =  self._node_graphics_objects.inverse[item]
                return node_id
            except KeyError:
                continue
        return

    def edgeAt(self, position: QPointF) -> tuple[NodeId, NodeId, tuple[str, str]] | None:
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                edge_id =  self._link_graphics_objects.inverse[item]
                return edge_id
            except KeyError:
                continue
        return

    def inletAt(self, position: QPointF) -> tuple[NodeId, str] | None:
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                inlet_id = self._inlet_graphics_objects.inverse[item]
                return inlet_id
            except KeyError:
                continue

    def outletAt(self, position: QPointF) -> tuple[NodeId, str] | None:
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                outlet_id = self._outlet_graphics_objects.inverse[item]
                return outlet_id
            except KeyError:
                continue

    def layout(self):
        from pylive.utils.graph_layout import hiearchical_layout_with_nx
        pos = hiearchical_layout_with_nx(self._model.G, scale=100)
        for N, (x, y) in pos.items():
            widget = self.nodeGraphicsObject(N)
            widget.setPos(x, y)

    @override
    def sendEvent(self, item:QGraphicsItem, event:QEvent)->bool:
        print("send event")
        return super().sendEvent(item, event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if outlet_id:=self.outletAt(event.scenePos()):
            node_id, outlet_key = outlet_id
            self.tool = GraphLinkTool(self)
            self.tool.startFromOutlet(node_id, outlet_key)
        elif inlet_id:=self.inletAt(event.scenePos()):
            node_id, inlet_key = inlet_id
            self.tool = GraphLinkTool(self)
            self.tool.startFromInlet(node_id, inlet_key)
        elif node_id:=self.nodeAt(event.scenePos()):
            super().mousePressEvent(event)
        elif edge_id:=self.edgeAt(event.scenePos()):
            super().mousePressEvent(event)


class GraphLinkTool(QObject):
    def __init__(self, graphscene:NXNetworkScene):
        super().__init__(parent=graphscene)
        import typing
        self._graphscene = graphscene
        self.loop = QEventLoop()
        self.draft:BaseLinkItem|None = None
        self.source_node_id:NodeId
        self.source_key:str
        self.direction:Literal['forward', 'backward'] = 'forward'

    def graphscene(self)->NXNetworkScene:
        return self._graphscene

    def startFromOutlet(self, node_id:NodeId, key:str):
        link = self.graphscene().delegate.createLink(node_id, None, (key, None))
        self.draft = link
        assert self.draft
        self.draft.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.draft.setAcceptHoverEvents(False)
        self.draft.setEnabled(False)
        self.draft.setActive(False)
        self.graphscene().addItem(self.draft)

        self.source_node_id = node_id
        self.source_key = key

        ### start event loop
        app = QApplication.instance()
        assert isinstance(app, QGuiApplication)
        self.direction = 'forward'
        app.installEventFilter(self)
        self.loop.exec()
        app.removeEventFilter(self)

    def startFromInlet(self, node_id:NodeId, key:str):
        self.draft = self.graphscene().delegate.createLink(None, node_id, (None, key))
        assert self.draft
        # self.draft.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        # self.draft.setAcceptHoverEvents(False)
        # self.draft.setEnabled(False)
        # self.draft.setActive(False)
        self.graphscene().addItem(self.draft)
        
        self.source_node_id = node_id
        self.source_key = key

        ### start event loop
        app = QApplication.instance()
        assert isinstance(app, QGuiApplication)
        self.direction = 'backward'
        app.installEventFilter(self)
        self.loop.exec()
        app.removeEventFilter(self)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        ...

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        assert self.draft is not None
        match self.direction:
            case 'forward':
                assert self.source_node_id is not None
                if target := self.graphscene().inletAt(event.scenePos()):
                    target_node_id, target_key = target
                    self.draft.move(
                        self.graphscene().outletGraphicsObject(self.source_node_id, self.source_key),
                        self.graphscene().inletGraphicsObject(target_node_id, target_key)
                    )
                else:
                    self.draft.move(
                        self.graphscene().outletGraphicsObject(self.source_node_id, self.source_key), 
                        event.scenePos()
                    )

            case 'backward':
                assert self.source_node_id is not None
                if target := self.graphscene().outletAt(event.scenePos()):
                    target_node_id, target_key = target
                    self.draft.move(
                        self.graphscene().outletGraphicsObject(target_node_id, target_key),
                        self.graphscene().inletGraphicsObject(self.source_node_id, self.source_key)
                    )
                else:
                    self.draft.move(
                        event.scenePos(),
                        self.graphscene().inletGraphicsObject(self.source_node_id, self.source_key)
                    )

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        assert self.draft is not None
        scene = self.graphscene()
        self.graphscene().removeItem(self.draft)
        model = scene.model()
        assert model is not None
        match self.direction:
            case 'forward':
                assert self.source_node_id is not None
                if inlet_id := self.graphscene().inletAt(event.scenePos()):
                    inlet_node_id, inlet_key = inlet_id
                    model.addEdge(self.source_node_id, inlet_node_id, (self.source_key, inlet_key))
                else:
                    pass

            case 'backward':
                assert self.source_node_id is not None
                if outlet_id := self.graphscene().outletAt(event.scenePos()):
                    outlet_node_id, outlet_key = outlet_id
                    model.addEdge(outlet_id, self.source_node_id, (outlet_key, self.source_key))
                else:
                    pass

        
        self.loop.exit()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        match event.type():
            case QEvent.Type.GraphicsSceneMouseMove:
                self.mouseMoveEvent(cast(QGraphicsSceneMouseEvent, event))
                return True
            case QEvent.Type.GraphicsSceneMouseRelease:
                self.mouseReleaseEvent(cast(QGraphicsSceneMouseEvent, event))
                return True
            case _:
                pass
        return super().eventFilter(watched, event)


###########################
# Active Graphics Objects #
###########################
# class InletGraphicsObject(PortShape):
#     def __init__(self, name: str):
#         super().__init__(name=f"{inlet_id[1]}")


# class OutletGraphicsObject(PortShape):
#     def __init__(self, name: str):
#         super().__init__(name=f"{outlet_id[1]}")

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


class StandardGraphFactory:
    def createNode(self, node_id:NodeId)->BaseNodeItem:
        node = StandardNodeItem()
        
        labelitem = QGraphicsTextItem(f"{node_id}")
        labelitem.adjustSize()
        labelitem.setPos(0,-2)
        labelitem.setParentItem(node)

        node.setGeometry(QRectF(0,0,labelitem.textWidth(),20))
        # print(node.geometry())


        return node

    def createInlet(self, parent_node:QGraphicsItem, node_id:NodeId, key:str)->QGraphicsItem:
        assert isinstance(key, str)
        inlet = PortShape(f"{key}")
        
        inlet.setParentItem(parent_node)
        return inlet

    def createOutlet(self, parent_node:QGraphicsItem, node_id:NodeId, key:str)->QGraphicsItem:
        assert isinstance(key, str)
        outlet = PortShape(f"{key}")
        outlet.setParentItem(parent_node)
        return outlet

    def createLink(self, u:NodeId|None, v:NodeId|None, k:tuple[str|None, str|None])->BaseLinkItem:
        assert isinstance(k, tuple)
        link = ArrowLinkShape(f"{k[1]}" if k[1] else "")
        link.setZValue(-1)
        return link


###########
# EXAMPLE #
###########
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # setup main window
    view = QGraphicsView()
    view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
    view.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
    view.setWindowTitle("NXNetworkScene")
    view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    # create graph scene
    graph = NXGraphModel()
    graph.addNode("N1", inlets=["in"], outlets=["out"])
    graph.addNode("N2", inlets=["in"], outlets=["out"])
    graph.addNode("N3", inlets=["in"], outlets=["out"])
    graph.addEdge("N1", "N2", ("out", "in"))
    selection = NXGraphSelectionModel(graph)


    scene = NXNetworkScene(graph, selection)
    scene.setSceneRect(QRectF(-400, -400, 800, 800))
    view.setScene(scene)



    # show window
    view.show()
    sys.exit(app.exec())
