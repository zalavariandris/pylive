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

from pylive.NetworkXGraphEditor.nx_graph_shapes import (
    NodeShape,
    LinkShape,
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
type SourceId = tuple[NodeId, str]
type TargetId = tuple[NodeId, str]
type EdgeId = tuple[Hashable, Hashable, Hashable]


def edgeSource(e: EdgeId) -> SourceId:
    u, v, (o, i) = e
    return (u, o)


def edgeTarget(e: EdgeId) -> TargetId:
    u, v, (o, i) = e
    return (v, i)


class NXNetworkScene(QGraphicsScene):
    def __init__(self, model: NXGraphModel, selection_model: NXGraphSelectionModel):
        super().__init__()
        # configure QGraphicsScene
        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        # store model widget relations
        self._node_graphics_objects: bidict[NodeId, NodeGraphicsObject] = bidict()
        self._source_graphics_objects: bidict[SourceId, OutletGraphicsObject] = bidict()
        self._target_graphics_objects: bidict[TargetId, InletGraphicsObject] = bidict()
        self._link_graphics_objects: bidict[EdgeId, LinkGraphicsObject] = bidict()
        self._draft_link: LinkGraphicsObject | None = None

        # draft link: # TODO: consider moving it to the GraphView.
        # GraphView is supposed to be responsible for user interactions
        self.draft: LinkShape | None = None  # todo use the widget itself?

        # set model
        self._model = model
        _ = self._model.nodesAdded.connect(
            lambda nodes: [self.onNodeCreated(n) for n in nodes]
        )
        _ = self._model.nodesAboutToBeRemoved.connect(
            lambda nodes: [self.onNodeDeleted(n) for n in nodes]
        )
        _ = self._model.edgesAdded.connect(
            lambda edges: [self.onEdgeCreated(e) for e in edges]
        )
        _ = self._model.edgesAboutToBeRemoved.connect(
            lambda edges: [self.onEdgeDeleted(e) for e in edges]
        )

        # set selection model
        self._selection_model = selection_model

        @self.selectionChanged.connect
        def update_selection_model():
            assert self._selection_model
            selected_nodes = [
                self._node_graphics_objects.inverse[cast(NodeGraphicsObject, node)]
                for node in self.selectedItems()
                if node in self._node_graphics_objects.values()
            ]
            self._selection_model.setSelectedNodes(selected_nodes)

        @selection_model.selectionChanged.connect
        def update_scene_selection(selected: set[Hashable], deselected: set[Hashable]):
            selected_widgets = [self.nodeGraphicsObject(n) for n in selected]
            deselected_widgets = [self.nodeGraphicsObject(n) for n in deselected]
            self.blockSignals(True)
            for widget in selected_widgets:
                widget.setSelected(True)

            for widget in deselected_widgets:
                widget.setSelected(False)
            self.blockSignals(False)
            self.selectionChanged.emit()

        # populate with initial model
        self.traverseGraphAndPopulateGraphicsObjects()
        self.layout()

    def traverseGraphAndPopulateGraphicsObjects(self):
        allNodeIds: list[NodeId] = self._model.nodes()

        # First create all the nodes.
        for nodeId in allNodeIds:
            self.onNodeCreated(nodeId)

        for e in self._model.edges():
            self.onEdgeCreated(e)

    def linkGraphicsObject(self, e: EdgeId) -> "LinkGraphicsObject":
        return self._link_graphics_objects[e]

    def nodeGraphicsObject(self, n: NodeId) -> "NodeGraphicsObject":
        return self._node_graphics_objects[n]

    def targetGraphicsObject(self, targetId: TargetId) -> QGraphicsItem:
        return self._target_graphics_objects[targetId]

    def sourceGraphicsObject(self, sourceId: SourceId) -> QGraphicsItem:
        return self._source_graphics_objects[sourceId]

    ### Handle Model Signals >>>
    def onEdgeDeleted(self, e: tuple[Hashable, Hashable, Hashable]):
        sourceId = e[0], f"{e[2][0]}"
        targetId = e[1], f"{e[2][1]}"
        self.removeItem(self.linkGraphicsObject(e))
        if e in self._link_graphics_objects:
            del self._link_graphics_objects[e]

    def onEdgeCreated(self, e: tuple[Hashable, Hashable, Hashable]):
        sourceId = e[0], f"{e[2][0]}"
        targetId = e[1], f"{e[2][1]}"
        link = LinkGraphicsObject(e)
        link.setLabelText(f"{e[2]}")

        self._link_graphics_objects[e] = link
        self.addItem(link)

        link.move(
            self.sourceGraphicsObject(sourceId),
            self.targetGraphicsObject(targetId),
        )

    def onNodeCreated(self, n: Hashable):
        node = NodeGraphicsObject(n, inlets=[], outlets=[])
        self._node_graphics_objects[n] = node
        self.addItem(self.nodeGraphicsObject(n))

        if self._model.hasNodeProperty(n, "inlets"):
            inletNames = self._model.getNodeProperty(n, "inlets")
            assert isinstance(inletNames, list) and all(
                isinstance(_, str) for _ in inletNames
            )
            for inletName in inletNames:
                inlet = self.onInletCreated(n, inletName)

        if self._model.hasNodeProperty(n, "outlets"):
            outletNames = self._model.getNodeProperty(n, "outlets")
            assert isinstance(outletNames, list) and all(
                isinstance(_, str) for _ in outletNames
            )
            for outletName in outletNames:
                outlet_graphics_object = self.onOutletCreated(n, outletName)

    def onOutletCreated(self, n: Hashable, source_name: str):
        sourceId: SourceId = (n, source_name)
        node = self.nodeGraphicsObject(n)
        outlet = OutletGraphicsObject((n, source_name))
        node._addOutlet(outlet)
        self._source_graphics_objects[(n, source_name)] = outlet
        return outlet

    def onInletCreated(self, n: Hashable, target_name: str):
        target_id: TargetId = (n, target_name)
        node = self.nodeGraphicsObject(n)
        inlet = InletGraphicsObject(target_id)
        node._addInlet(inlet)
        self._target_graphics_objects[target_id] = inlet
        return inlet

    def makeDraftLink(self):
        self.draft = LinkShape()
        self.draft.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.draft.setAcceptHoverEvents(False)
        self.draft.setEnabled(False)
        self.draft.setActive(False)
        self.addItem(self.draft)

    def resetDraftLink(self):
        assert self.draft is not None
        self.removeItem(self.draft)
        self.draft = None

    def onNodeDeleted(self, n: Hashable):
        if n in self._node_graphics_objects:
            node_graphics_object = self.nodeGraphicsObject(n)
            raise NotImplementedError()

    def onModelReset(self):
        self._target_graphics_objects.clear()
        self._source_graphics_objects.clear()
        self._link_graphics_objects.clear()
        self._node_graphics_objects.clear()
        self.clear()

        self.traverseGraphAndPopulateGraphicsObjects()

    ### <<< Handle Model Signals
    def sourceAt(self, position: QPointF) -> SourceId | None:
        # find source (model) under mouse
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                return self._source_graphics_objects.inverse[
                    cast(OutletGraphicsObject, item)
                ]
            except KeyError:
                return None

    def targetAt(self, position: QPointF) -> TargetId | None:
        # find source (model) under mouse
        for item in self.items(position, deviceTransform=QTransform()):
            try:
                return self._target_graphics_objects.inverse[
                    cast(InletGraphicsObject, item)
                ]
            except KeyError:
                return None

    # def _findGraphItemAt(self, klass, position: QPointF):
    #     # find outlet under mouse
    #     for item in self.items(position, deviceTransform=QTransform()):
    #         if isinstance(item, klass):
    #             return item

    # def _outletEditorAt(self, position: QPointF) -> "OutletGraphicsObject":
    #     return cast(
    #         OutletGraphicsObject,
    #         self._findGraphItemAt(OutletGraphicsObject, position),
    #     )

    # def _inletEditorAt(self, position: QPointF) -> "InletGraphicsObject":
    #     return cast(
    #         InletGraphicsObject,
    #         self._findGraphItemAt(InletGraphicsObject, position),
    #     )

    # def nodeAt(self, position: QPointF) -> "NodeGraphicsObject":
    #     return cast(
    #         NodeGraphicsObject,
    #         self._findGraphItemAt(NodeGraphicsObject, position),
    #     )

    # def linkAt(self, position: QPointF) -> "LinkGraphicsObject":
    #     return cast(
    #         LinkGraphicsObject,
    #         self._findGraphItemAt(LinkGraphicsObject, position),
    #     )

    def layout(self):
        from pylive.utils.graph_layout import hiearchical_layout_with_nx

        pos = hiearchical_layout_with_nx(self._model.G, scale=100)
        for N, (x, y) in pos.items():
            widget = self.nodeGraphicsObject(N)
            widget.setPos(x, y)

    # def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     item = self.itemAt(event.scenePos(), QTransform())
    #     if item in self._node_graphics_objects.values():
    #         print("node clicked")
    #     else:
    #         return super().mousePressEvent(event)


###########################
# Active Graphics Objects #
###########################


class OutletGraphicsObject(PortShape):
    def __init__(self, sourceId: SourceId):
        super().__init__(label=f"{sourceId}")
        self.sourceId = sourceId

    def graphscene(self) -> "NXNetworkScene":
        return cast(NXNetworkScene, self.scene())

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.graphscene().makeDraftLink()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        draft = self.graphscene().draft
        assert draft is not None

        # if inletId := self.graphscene()._inletEditorAt(event.scenePos()):
        if inletId := self.graphscene().targetAt(event.scenePos()):
            draft.move(self, self.graphscene().targetGraphicsObject(inletId))
        else:
            draft.move(self, event.scenePos())
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.graphscene().resetDraftLink()

        if targetId := self.graphscene().targetAt(event.scenePos()):
            scene = self.graphscene()

            scene._model.addEdge(
                self.sourceId[0], targetId[0], (self.sourceId[1], targetId[1])
            )

        return super().mouseReleaseEvent(event)


class InletGraphicsObject(PortShape):
    def __init__(self, targetId: TargetId):
        super().__init__(label=f"{targetId}")
        self.targetId = targetId

    def graphscene(self) -> "NXNetworkScene":
        return cast(NXNetworkScene, self.scene())

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.graphscene().makeDraftLink()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        draft = self.graphscene().draft
        assert draft is not None

        if sourceId := self.graphscene().sourceAt(event.scenePos()):
            draft.move(self.graphscene().sourceGraphicsObject(sourceId), self)
        else:
            draft.move(event.scenePos(), self)
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.graphscene().resetDraftLink()

        if sourceId := self.graphscene().sourceAt(event.scenePos()):
            scene = self.graphscene()
            scene._model.addEdge(
                sourceId[0], self.targetId[0], (sourceId[1], self.targetId[1])
            )

        return super().mouseReleaseEvent(event)


class NodeGraphicsObject(NodeShape):
    def __init__(
        self,
        n: NodeId,
        inlets: list[InletGraphicsObject],
        outlets: list[OutletGraphicsObject],
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(
            title=f"'{n}'",
            inlets=inlets,
            outlets=outlets,
            parent=parent,
        )
        self._n = n
        self.setAcceptHoverEvents(False)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.moveLinks()
        return super().itemChange(change, value)

    def graphscene(self) -> "NXNetworkScene":
        return cast(NXNetworkScene, self.scene())

    def moveLinks(self):
        """responsible to update connected link position"""
        model = self.graphscene()._model
        all_edges = model.inEdges(self._n) + model.outEdges(self._n)
        for e in all_edges:
            # assert isinstance(e[2], tuple) and len(e[2]) == 2
            # u, v, (o, i) = e
            sourceId = e[0], f"{e[2][0]}"
            targetId = e[1], f"{e[2][1]}"
            self.graphscene()

            outlet = self.graphscene().sourceGraphicsObject(sourceId)
            inlet = self.graphscene().targetGraphicsObject(targetId)
            edge = self.graphscene().linkGraphicsObject((sourceId, targetId))
            edge.move(outlet, inlet)


class LinkGraphicsObject(LinkShape):
    def __init__(self, e: EdgeId, parent: QGraphicsItem | None = None):
        super().__init__(label=f"{e}", parent=parent)
        self._e = e
        self.setZValue(-1)

    def graphscene(self) -> "NXNetworkScene":
        return cast(NXNetworkScene, self.scene())

    def boundingRect(self) -> QRectF:
        return super().boundingRect().adjusted(-50, -50, 50, 50)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        ...
        # if event.button() == Qt.MouseButton.LeftButton:
        #     self.grabMouse()
        # else:
        #     self.ungrabMouse()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        print("mouse move event")
        _, thisTargetId = self._e
        if outletId := self.graphscene().sourceAt(event.scenePos()):
            self.move(self.graphscene().sourceGraphicsObject(outletId), self)
        else:
            self.move(
                event.scenePos(),
                self.graphscene().targetGraphicsObject(thisTargetId),
            )
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        model = self.graphscene()._model
        target = self.graphscene().targetAt(event.scenePos())
        thisSourceId, thisTargetId = self._e
        if Qt.MouseButton.RightButton in event.buttons():
            # cancel
            self.move(
                self.graphscene().sourceGraphicsObject(thisSourceId),
                self.graphscene().targetGraphicsObject(thisTargetId),
            )
            self.ungrabMouse()
        else:
            # TODO: add an addMethod to the graphview, to convert from the graph edge representation to the model;s

            if target and target != self._e[1]:
                u, o = thisSourceId
                v, i = thisTargetId
                model.removeEdge(u, v, (o, i))
                model.addEdge(thisSourceId[0], target[0], (thisTargetId[1], target[1]))

            elif target == None:
                u, o = thisSourceId
                v, i = thisTargetId
                model.removeEdge(u, v, (o, i))

            elif target == thisTargetId:
                # cancel

                self.move(
                    self.graphscene().sourceGraphicsObject(thisSourceId),
                    self.graphscene().targetGraphicsObject(thisTargetId),
                )
            else:
                raise Exception("")

            return super().mouseReleaseEvent(event)


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
    graph.addNode("N1", outlets=["out"])
    graph.addNode("N2", inlets=["in"])
    graph.addNode("N3", inlets=["in"], outlets=["out"])
    graph.addEdge("N1", "N2", ("out", "in"))
    graphscene = NXNetworkScene(graph, NXGraphSelectionModel(graph))
    graphscene.setSceneRect(QRectF(-400, -400, 800, 800))
    view.setScene(graphscene)

    # graphscene.addItem(GraphicsVertexItem("HWELLO"))

    # show window
    view.show()
    sys.exit(app.exec())
