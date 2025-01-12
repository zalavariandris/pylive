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
    NodeShape,
    ArrowLinkShape,
    RoundedLinkShape,
    PortShape,
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
type OutletId = tuple[Hashable, Hashable]
type InletId = tuple[Hashable, Hashable]
type EdgeId = tuple[Hashable, Hashable, tuple[str,str]]


class NXNetworkScene(QGraphicsScene):
    def __init__(self, model: NXGraphModel, selection_model: NXGraphSelectionModel):
        super().__init__()

        self._model: NXGraphModel | None = None
        self._selection_model:NXGraphSelectionModel|None = None

        # configure QGraphicsScene
        # self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        # store model widget relations
        self._node_graphics_objects: bidict[NodeId, NodeGraphicsObject] = bidict()
        self._outlet_graphics_objects: bidict[OutletId, OutletGraphicsObject] = bidict()
        self._inlet_graphics_objects: bidict[InletId, InletGraphicsObject] = bidict()
        self._link_graphics_objects: bidict[EdgeId, LinkGraphicsObject] = bidict()
        self._draft_link: LinkGraphicsObject | None = None

        # draft link: # TODO: consider moving it to the GraphView.
        # GraphView is supposed to be responsible for user interactions
        # self.draft: RoundedLinkShape | None = None  # todo use the widget itself?

        # set model
        # populate with initial model
        
        self.setModel(model)
        self.setSelectionModel(selection_model)

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
            self._node_graphics_objects.inverse[cast(NodeGraphicsObject, node)]
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
        self.onNodesCreated([n for n in self._model.nodes()])
        self.onEdgesCreated([cast(EdgeId, e) for e in self._model.edges()])

        # layout items
        self.layout()

    def model(self):
        return self._model

    ### <<< Map the interactive graphics ids to widgets
    def nodeGraphicsObject(self, nodeId: NodeId) -> QGraphicsItem:
        return self._node_graphics_objects[nodeId]

    def outletGraphicsObject(self, outlet_id: OutletId) -> QGraphicsItem:
        return self._outlet_graphics_objects[outlet_id]

    def inletGraphicsObject(self, inlet_id: InletId) -> QGraphicsItem:
        return self._inlet_graphics_objects[inlet_id]

    def linkGraphicsObject(self, e: EdgeId) -> "LinkGraphicsObject":
        return self._link_graphics_objects[e]

    ### <<< Handle Model Signals
    def onNodesCreated(self, nodes: list[Hashable]):
        assert self._model
        for n in nodes:
            node = NodeGraphicsObject(n, inlets=[])
            self._node_graphics_objects[n] = node
            self.addItem(self.nodeGraphicsObject(n))

            if not self._model.hasNodeProperty(n, "inlets"):
                raise ValueError("Nodes must have an 'inlets' attribute")

            if not self._model.hasNodeProperty(n, "outlets"):
                raise ValueError("Nodes must have an 'outlets' attribute")

            inletNames = self._model.getNodeProperty(n, "inlets")
            assert isinstance(inletNames, list) and all(
                isinstance(_, str) for _ in inletNames
            )
            for inletName in inletNames:
                inlet_id: InletId = (n, inletName)
                node = cast(NodeGraphicsObject, self.nodeGraphicsObject(n))
                inlet = InletGraphicsObject(inlet_id)
                node._addInlet(inlet)
                self._inlet_graphics_objects[inlet_id] = inlet


            outlet_names = self._model.getNodeProperty(n, "outlets")
            assert isinstance(outlet_names, list) and all(
                isinstance(_, str) for _ in outlet_names
            )
            for outlet_name in outlet_names:
                outlet_id: OutletId = (n, outlet_name)
                node = cast(NodeGraphicsObject, self.nodeGraphicsObject(n))
                outlet = OutletGraphicsObject(outlet_id)
                node._addOutlet(outlet)
                self._outlet_graphics_objects[outlet_id] = outlet

    def onEdgesDeleted(self, edges: list[tuple[Hashable, Hashable, Hashable]]):
        for e in edges:
            assert isinstance(e[2], tuple)
            self.removeItem(self.linkGraphicsObject(cast(EdgeId, e)))
            if e in self._link_graphics_objects:
                del self._link_graphics_objects[e]

    def onEdgesCreated(self, edges: list[EdgeId]):
        for e in edges:
            link = LinkGraphicsObject(e)
            link.setLabelText(f"{e[2]}")

            self._link_graphics_objects[e] = link
            self.addItem(link)

            u, v, (o, i) = e
            link.move(
                self.outletGraphicsObject( (u, o) ),
                self.inletGraphicsObject((v, i))
            )

    def onNodesDeleted(self, nodes: list[Hashable]):
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
        self.onNodesCreated([n for n in self._model.nodes()])
        self.onEdgesCreated([cast(EdgeId, e) for e in self._model.edges()])

        # layout items
        self.layout()

    def onSelectionChanged(self, selected: set[Hashable], deselected: set[Hashable]):
        selected_widgets = [self.nodeGraphicsObject(n) for n in selected]
        deselected_widgets = [self.nodeGraphicsObject(n) for n in deselected]
        self.blockSignals(True)
        for widget in selected_widgets:
            widget.setSelected(True)

        for widget in deselected_widgets:
            widget.setSelected(False)
        self.blockSignals(False)
        self.selectionChanged.emit()

    ### <<< Handle Model Signals

    # ### linking tools ###
    # def makeDraftLink(self):
    #     self.draft = RoundedLinkShape("")
    #     self.draft.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
    #     self.draft.setAcceptHoverEvents(False)
    #     self.draft.setEnabled(False)
    #     self.draft.setActive(False)
    #     self.addItem(self.draft)

    # def resetDraftLink(self):
    #     assert self.draft is not None
    #     self.removeItem(self.draft)
    #     self.draft = None

    def nodeAt(self, position: QPointF) -> NodeId | None:
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                node_id =  self._node_graphics_objects.inverse[item]
                return node_id
            except KeyError:
                continue
        return

    def edgeAt(self, position: QPointF) -> EdgeId | None:
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                edge_id =  self._link_graphics_objects.inverse[item]
                return edge_id
            except KeyError:
                continue
        return

    def inletAt(self, position: QPointF) -> InletId | None:
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                inlet_id = self._inlet_graphics_objects.inverse[item]
                return inlet_id
            except KeyError:
                continue

    def outletAt(self, position: QPointF) -> OutletId | None:
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
            self.tool = GraphLinkTool(self)
            self.tool.startFromOutlet(outlet_id)
        elif inlet_id:=self.inletAt(event.scenePos()):
            self.tool = GraphLinkTool(self)
            self.tool.startFromInlet(inlet_id)
        elif node_id:=self.nodeAt(event.scenePos()):
            super().mousePressEvent(event)
        elif edge_id:=self.edgeAt(event.scenePos()):
            super().mousePressEvent(event)
        


class GraphLinkTool(QObject):
    def __init__(self, graphscene:NXNetworkScene):
        super().__init__(parent=graphscene)
        self._graphscene = graphscene
        self.loop = QEventLoop()
        self.draft:LinkGraphicsObject|None = None
        self.outlet_id:OutletId|None = None
        self.inlet_id:InletId|None = None
        self.direction:Literal['forward', 'backward'] = 'forward'

    def graphscene(self)->NXNetworkScene:
        return self._graphscene

    def startFromOutlet(self, outletId:OutletId):
        self.draft = LinkGraphicsObject("")
        self.draft.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.draft.setAcceptHoverEvents(False)
        self.draft.setEnabled(False)
        self.draft.setActive(False)
        self.graphscene().addItem(self.draft)

        self.outlet_id = outletId

        ### start event loop
        app = QApplication.instance()
        assert isinstance(app, QGuiApplication)
        self.direction = 'forward'
        app.installEventFilter(self)
        self.loop.exec()
        app.removeEventFilter(self)

    def startFromInlet(self, inlet_id:InletId):
        self.draft = LinkGraphicsObject("")
        self.draft.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.draft.setAcceptHoverEvents(False)
        self.draft.setEnabled(False)
        self.draft.setActive(False)
        self.graphscene().addItem(self.draft)

        self.inlet_id = inlet_id

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
                assert self.outlet_id is not None
                if inlet_id := self.graphscene().inletAt(event.scenePos()):
                    self.draft.move(
                        self.graphscene().outletGraphicsObject(self.outlet_id),
                        self.graphscene().inletGraphicsObject(inlet_id)
                    )
                else:
                    self.draft.move(
                        self.graphscene().outletGraphicsObject(self.outlet_id), 
                        event.scenePos()
                    )

            case 'backward':
                assert self.inlet_id is not None
                if outlet_id := self.graphscene().outletAt(event.scenePos()):
                    self.draft.move(
                        self.graphscene().outletGraphicsObject(outlet_id),
                        self.graphscene().inletGraphicsObject(self.inlet_id)
                    )
                else:
                    self.draft.move(
                        event.scenePos(),
                        self.graphscene().inletGraphicsObject(self.inlet_id)
                    )

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        assert self.draft is not None
        scene = self.graphscene()
        model = scene.model()
        assert model is not None
        match self.direction:
            case 'forward':
                assert self.outlet_id is not None
                if inlet_id := self.graphscene().inletAt(event.scenePos()):
                    model.addEdge(self.outlet_id[0], inlet_id[0], (self.outlet_id[1], inlet_id[1]))
                else:
                    pass

            case 'backward':
                assert self.inlet_id is not None
                if outlet_id := self.graphscene().outletAt(event.scenePos()):
                    model.addEdge(outlet_id[0], self.inlet_id[0], (outlet_id[1], self.inlet_id[1]))
                else:
                    pass

        self.graphscene().removeItem(self.draft)
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
class InletGraphicsObject(PortShape):
    def __init__(self, inlet_id: InletId):
        super().__init__(name=f"{inlet_id[1]}")


class OutletGraphicsObject(PortShape):
    def __init__(self, outlet_id: OutletId):
        super().__init__(name=f"{outlet_id[1]}")


class NodeGraphicsObject(NodeShape):
    def __init__(
        self,
        n: NodeId,
        inlets: list[InletGraphicsObject],
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(
            name=f"'{n}'",
            inlets=inlets,
            outlets=[],
            parent=parent,
        )
        self.nodeId = n
        # Enable selection and movement
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsFocusable, True)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.moveLinks()
        return super().itemChange(change, value)

    def graphscene(self) -> "NXNetworkScene":
        return cast(NXNetworkScene, self.scene())

    def moveLinks(self):
        """responsible to update connected link position"""
        model = self.graphscene().model()
        in_out_edges = model.inEdges(self.nodeId) + model.outEdges(self.nodeId)
        for edge_id in in_out_edges:
            u, v, (o, i) = edge_id
            self.graphscene()
            node = self.graphscene().nodeGraphicsObject(u)
            outlet = self.graphscene().outletGraphicsObject( (u, o) )
            inlet = self.graphscene().inletGraphicsObject((v, i))
            edge = self.graphscene().linkGraphicsObject(edge_id)
            bbox = node.boundingRect()
            edge.move(outlet, inlet)


class LinkGraphicsObject(ArrowLinkShape):
    def __init__(self, e: EdgeId, parent: QGraphicsItem | None = None):
        super().__init__(label=f"{e}", parent=parent)
        # self.edge_id = e
        self.setZValue(-1)

    # def graphscene(self) -> "NXNetworkScene":
    #     return cast(NXNetworkScene, self.scene())

    # def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     ...
    #     # if event.button() == Qt.MouseButton.LeftButton:
    #     #     self.grabMouse()
    #     # else:
    #     #     self.ungrabMouse()

    # def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     if inlet_id := self.graphscene().inletAt(event.scenePos()):
    #         u, v, k = self.edge_id
    #         self.move(
    #             self.graphscene().nodeGraphicsObject(u), 
    #             self.graphscene().inletGraphicsObject(inlet_id))
    #     else:
    #         u, v, k = self.edge_id
    #         self.move(
    #             self.graphscene().nodeGraphicsObject(u), 
    #             event.scenePos())
    #     return super().mouseMoveEvent(event)

    # def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     model = self.graphscene().model()
    #     assert model
    #     inlet_id:InletId|None = self.graphscene().inletAt(event.scenePos())
    #     print("mouseReleaseEvent")
    #     u, v, k = self.edge_id
    #     if inlet_id and inlet_id != (v, k):
    #         # connect to other inlet
    #         model.removeEdge(u, v, k)
    #         model.addEdge(u, inlet_id[0], inlet_id[1])

    #     elif inlet_id == None:
    #         # remove
    #         model.removeEdge(u, v, k)

    #     elif inlet_id == (v, k):
    #         # cancel
    #         self.move(
    #             self.graphscene().nodeGraphicsObject(u),
    #             self.graphscene().inletGraphicsObject((v, k))
    #         )
    #     else:
    #         raise Exception("")

    #     return super().mouseReleaseEvent(event)


###########
# EXAMPLE #
###########
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # setup main window
    view = QGraphicsView()
    view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
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
    graphscene = NXNetworkScene(graph, NXGraphSelectionModel(graph))
    graphscene.setSceneRect(QRectF(-400, -400, 800, 800))
    view.setScene(graphscene)

    # graphscene.addItem(GraphicsVertexItem("HWELLO"))

    # show window
    view.show()
    sys.exit(app.exec())
