from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.NetworkXGraphEditor.nx_graph_shapes import NodeShape, LinkShape, PortShape

from pylive.NetworkXGraphEditor.nx_graph_scene import NXGraphScene, NodeId, LinkId
from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel
from dataclasses import dataclass


@dataclass(frozen=True)
class OutletId:
    nodeId: NodeId
    name: str

@dataclass(frozen=True)
class InletId:
    nodeId: NodeId
    name: str


class NXNetworkScene(NXGraphScene):
    def __init__(self, model: NXGraphModel):
        self._inlet_graphics_objects: dict[
            InletId, InletGraphicsObject
        ] = dict()

        self._outlet_graphics_objects: dict[
            OutletId, OutletGraphicsObject
        ] = dict()
        super().__init__(model)

    def onNodeCreated(self, n: NodeId):
        inlet_names = (
            self._model.getNodeProperty(n, "inlets")
            if self._model.hasNodeProperty(n, "inlets")
            else []
        )

        inlets = []
        if self._model.hasNodeProperty(n, "inlets"):
            inletNames = self._model.getNodeProperty(n, "inlets")
            assert isinstance(inletNames, list) and all(
                isinstance(_, str) for _ in inletNames
            )
            for inletName in inletNames:
                inlet_graphics_object = InletGraphicsObject(
                    InletId(n, inletName)
                )
                self._inlet_graphics_objects[
                    InletId(n, inletName)
                ] = inlet_graphics_object
                inlets.append(inlet_graphics_object)

        outlets = []
        if self._model.hasNodeProperty(n, "outlets"):
            outletNames = self._model.getNodeProperty(n, "outlets")
            assert isinstance(outletNames, list) and all(
                isinstance(_, str) for _ in outletNames
            )
            for outletName in outletNames:
                outlet_graphics_object = OutletGraphicsObject(
                    OutletId(n, outletName)
                )
                self._outlet_graphics_objects[
                    OutletId(n, outletName)
                ] = outlet_graphics_object
                outlets.append(outlet_graphics_object)

        self._node_graphics_objects[n] = NodeGraphicsObject(
            n, inlets=inlets, outlets=outlets
        )

        self.addItem(self.nodeGraphicsObject(n))

    def inletGraphicsObject(self, i: InletId) -> "InletGraphicsObject":
        return self._inlet_graphics_objects[i]

    def outletGraphicsObject(self, o: OutletId) -> "OutletGraphicsObject":
        return self._outlet_graphics_objects[o]

    def sourceGraphicsObject(self, e:LinkId)->QGraphicsItem:
        u, v, (o, i) = e
        return self.outletGraphicsObject(OutletId(u, o))

    def targetGraphicsObject(self, e:LinkId)->QGraphicsItem:
        u, v, (o, i) = e
        return self.inletGraphicsObject(InletId(v, i))

    def isLinked(self, port: InletId | OutletId) -> bool:
        match port:
            case InletId():
                for u, v, (o, i) in self._model.inEdges(port.nodeId):
                    if i == port.name:
                        return True
            case OutletId():
                for u, v, (o, i) in self._model.outEdges(port.nodeId):
                    if o == port.name:
                        return True
        return False

    def outletAt(self, position: QPointF) -> "OutletGraphicsObject":
        return cast(
            OutletGraphicsObject,
            self._findGraphItemAt(OutletGraphicsObject, position),
        )

    def inletAt(self, position: QPointF) -> "InletGraphicsObject":
        return cast(
            InletGraphicsObject,
            self._findGraphItemAt(InletGraphicsObject, position),
        )


class OutletGraphicsObject(PortShape):
    def __init__(self, o: OutletId):
        super().__init__(label=f"{o.name}")
        self._o = o

    def graphscene(self) -> "NXGraphScene":
        return cast(NXNetworkScene, self.scene())

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.graphscene().makeDraftLink()
        self.grabMouse()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        draft = self.graphscene().draft
        assert draft is not None

        if inlet := self.graphscene().inletAt(event.scenePos()):
            draft.move(self, inlet)
        else:
            draft.move(self, event.scenePos())
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.ungrabMouse()
        self.graphscene().resetDraftLink()

        if inlet := self.graphscene().inletAt(event.scenePos()):
            scene = self.graphscene()
            scene._model.addEdge(
                self._o.nodeId, inlet._i.nodeId, (self._o.name, inlet._i.name)
            )

        return super().mouseReleaseEvent(event)

    def brush(self):
        brush = super().brush()
        if self.graphscene().isLinked(self._o):
            brush = self.palette().text()

        return brush


class InletGraphicsObject(PortShape):
    def __init__(self, i: InletId):
        super().__init__(label=f"{i.name}")
        self._i = i

    def graphscene(self) -> "NXGraphScene":
        return cast(NXNetworkScene, self.scene())

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.graphscene().makeDraftLink()
        self.grabMouse()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        draft = self.graphscene().draft
        assert draft is not None

        if outlet := self.graphscene().outletAt(event.scenePos()):
            draft.move(outlet, self)
        else:
            draft.move(event.scenePos(), self)
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.ungrabMouse()
        self.graphscene().resetDraftLink()

        if outlet := self.graphscene().outletAt(event.scenePos()):
            self.graphscene()._model.addEdge(
                outlet._o.nodeId, self._i.nodeId, (outlet._o.name, self._i.name)
            )

        return super().mouseReleaseEvent(event)

    def brush(self):
        brush = super().brush()
        if self.graphscene().isLinked(self._i):
            brush = self.palette().text()

        return brush


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

    def graphscene(self) -> "NXGraphScene":
        return cast(NXNetworkScene, self.scene())

    def itemChange(
        self, change: QGraphicsItem.GraphicsItemChange, value: Any
    ) -> Any:
        if (
            change
            == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged
        ):
            self.moveLinks()
        return super().itemChange(change, value)

    def moveLinks(self):
        """responsible to update connected link position"""
        model = self.graphscene()._model
        all_edges = model.inEdges(self._n) + model.outEdges(self._n)
        for e in all_edges:
            assert isinstance(e[2], tuple) and len(e[2]) == 2
            u, v, (o, i) = e
            self.graphscene()
            outlet = self.graphscene().outletGraphicsObject(OutletId(u, o))
            inlet = self.graphscene().inletGraphicsObject(InletId(v, i))
            edge = self.graphscene().linkGraphicsObject(e)
            edge.move(outlet, inlet)



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
    graphscene = NXNetworkScene(graph)
    graphscene.setSceneRect(QRectF(-400, -400, 800, 800))
    view.setScene(graphscene)

    # graphscene.addItem(GraphicsVertexItem("HWELLO"))

    # show window
    view.show()
    sys.exit(app.exec())
