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


ConnectionEnterType = QEvent.Type(QEvent.registerEventType())
ConnectionLeaveType = QEvent.Type(QEvent.registerEventType())
ConnectionMoveType = QEvent.Type(QEvent.registerEventType())
ConnectionDropType = QEvent.Type(QEvent.registerEventType())

import numpy as np
import networkx as nx


##################
# GRAPHICS ITEMS #
##################

from pylive.NetworkXGraphEditor.nx_graph_shapes import (
    NodeShape,
    LinkShape,
    PortShape,
)


##############
# GRAPHSCENE #
##############

from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel

from dataclasses import dataclass

type NodeId = Hashable


@dataclass(frozen=True)
class OutletId:
    nodeId: NodeId
    name: str


@dataclass(frozen=True)
class InletId:
    nodeId: NodeId
    name: str


type LinkId = tuple[NodeId, NodeId, tuple[str, str]]


class NXGraphScene(QGraphicsScene):
    def __init__(self, model: NXGraphModel):
        super().__init__()
        self._model = model
        self._node_graphics_objects: dict[NodeId, NodeGraphicsObject] = dict()
        self._inlet_graphics_objects: dict[
            InletId, InletGraphicsObject
        ] = dict()
        self._outlet_graphics_objects: dict[
            OutletId, OutletGraphicsObject
        ] = dict()
        self._link_graphics_objects: dict[LinkId, LinkGraphicsObject] = dict()
        self._draft_link: LinkGraphicsObject | None = None

        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        self._model.nodesAdded.connect(
            lambda nodes: [self.onNodeCreated(n) for n in nodes]
        )
        self._model.nodesAboutToBeRemoved.connect(
            lambda nodes: [self.onNodeDeleted(n) for n in nodes]
        )
        self._model.edgesAdded.connect(
            lambda edges: [self.onLinkCreated(e) for e in edges]
        )
        self._model.edgesAboutToBeRemoved.connect(
            lambda edges: [self.onLinkDeleted(e) for e in edges]
        )

        self.traverseGraphAndPopulateGraphicsObjects()
        self.draft: LinkShape | None = None  # todo use the widget itself
        self.layout()

    def traverseGraphAndPopulateGraphicsObjects(self):
        allNodeIds: list[NodeId] = self._model.nodes()

        # First create all the nodes.
        for nodeId in allNodeIds:
            self.onNodeCreated(nodeId)

        for e in self._model.edges():
            u, v, (o, i) = e
            assert u in self._node_graphics_objects
            assert v in self._node_graphics_objects
            assert (
                OutletId(u, o) in self._outlet_graphics_objects
            ), f"Node '{u}' has no outlet '{o}'!"
            assert (
                InletId(v, i) in self._inlet_graphics_objects
            ), f"Node '{v}' has no inlet '{i}'!"

            link = LinkGraphicsObject((u, v, (o, i)))
            self._link_graphics_objects[(u, v, (o, i))] = link
            self.addItem(link)

            link.move(
                self.outletGraphicsObject(OutletId(u, o)),
                self.inletGraphicsObject(InletId(v, i)),
            )

    def linkGraphicsObject(self, e: LinkId) -> "LinkGraphicsObject":
        return self._link_graphics_objects[e]

    def nodeGraphicsObject(self, n: NodeId) -> "NodeGraphicsObject":
        return self._node_graphics_objects[n]

    def inletGraphicsObject(self, i: InletId) -> "InletGraphicsObject":
        return self._inlet_graphics_objects[i]

    def outletGraphicsObject(self, o: OutletId) -> "OutletGraphicsObject":
        return self._outlet_graphics_objects[o]

    def updateAttachedNodes(self, e: LinkId, kind: Literal["in", "out"]):
        u, v, k = e
        match kind:
            case "in":
                if node := self._node_graphics_objects.get(u, None):
                    node.update()
            case "out":
                if node := self._node_graphics_objects.get(v, None):
                    node.update()

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

    ### Handle Model Signals >>>
    def onLinkDeleted(self, e: LinkId):
        self.removeItem(self.linkGraphicsObject(e))
        if e in self._link_graphics_objects:
            del self._link_graphics_objects[e]

        self.updateAttachedNodes(e, "in")
        self.updateAttachedNodes(e, "out")

    def onLinkCreated(self, e: LinkId):
        link = LinkGraphicsObject(e)
        self._link_graphics_objects[e] = link
        self.addItem(self.linkGraphicsObject(e))
        self.updateAttachedNodes(e, "in")
        self.updateAttachedNodes(e, "out")

        u, v, (o, i) = e
        link.move(
            self.outletGraphicsObject(OutletId(u, o)),
            self.inletGraphicsObject(InletId(v, i)),
        )

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

    def onNodeDeleted(self, n: NodeId):
        if n in self._node_graphics_objects:
            node_graphics_object = self._node_graphics_objects[n]
            raise NotImplementedError()

    def onModelReset(self):
        self._link_graphics_objects.clear()
        self._node_graphics_objects.clear()
        self.clear()

        self.traverseGraphAndPopulateGraphicsObjects()

    ### <<< Handle Model Signals
    def _findGraphItemAt(self, klass, position: QPointF):
        # find outlet under mouse
        for item in self.items(position, deviceTransform=QTransform()):
            if isinstance(item, klass):
                return item

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

    def nodeAt(self, position: QPointF) -> "NodeGraphicsObject":
        return cast(
            NodeGraphicsObject,
            self._findGraphItemAt(NodeGraphicsObject, position),
        )

    def linkAt(self, position: QPointF) -> "LinkGraphicsObject":
        return cast(
            LinkGraphicsObject,
            self._findGraphItemAt(LinkGraphicsObject, position),
        )

    def layout(self):
        def hiearchical_layout_with_grandalf(G, scale=1):
            import grandalf
            from grandalf.layouts import SugiyamaLayout

            g = grandalf.utils.convert_nextworkx_graph_to_grandalf(G)

            class defaultview(object):  # see README of grandalf's github
                w, h = scale, scale

            for v in g.C[0].sV:
                v.view = defaultview()
            sug = SugiyamaLayout(g.C[0])
            sug.init_all()  # roots=[V[0]])
            sug.draw()
            return {
                v.data: (v.view.xy[0], v.view.xy[1]) for v in g.C[0].sV
            }  # Extracts the positions

        def hiearchical_layout_with_nx(G, scale=100):
            for layer, nodes in enumerate(
                reversed(tuple(nx.topological_generations(G)))
            ):
                # `multipartite_layout` expects the layer as a node attribute, so add the
                # numeric layer value as a node attribute
                for node in nodes:
                    G.nodes[node]["layer"] = -layer

            # Compute the multipartite_layout using the "layer" node attribute
            pos = nx.multipartite_layout(
                G, subset_key="layer", align="horizontal"
            )
            for n, p in pos.items():
                pos[n] = p[0] * scale, p[1] * scale
            return pos

        pos = hiearchical_layout_with_nx(self._model.G, scale=100)
        for N, (x, y) in pos.items():
            widget = self.nodeGraphicsObject(N)
            widget.setPos(x, y)


###########################
# Active Graphics Objects #
###########################


class OutletGraphicsObject(PortShape):
    def __init__(self, o: OutletId):
        super().__init__(label=f"{o.name}")
        self._o = o

    def graphscene(self) -> "NXGraphScene":
        return cast(NXGraphScene, self.scene())

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
        return cast(NXGraphScene, self.scene())

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

    def itemChange(
        self, change: QGraphicsItem.GraphicsItemChange, value: Any
    ) -> Any:
        if (
            change
            == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged
        ):
            self.moveLinks()
        return super().itemChange(change, value)

    def graphscene(self) -> "NXGraphScene":
        return cast(NXGraphScene, self.scene())

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


class LinkGraphicsObject(LinkShape):
    def __init__(self, e: LinkId, parent: QGraphicsItem | None = None):
        u, v, (o, i) = e
        super().__init__(label=f"{o}->{i}", parent=parent)
        self._e = e
        self.setZValue(-1)

    def graphscene(self) -> "NXGraphScene":
        return cast(NXGraphScene, self.scene())

    def boundingRect(self) -> QRectF:
        return super().boundingRect().adjusted(-50, -50, 50, 50)


###########
# EXAMPLE #
###########
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # setup main window
    view = QGraphicsView()
    view.setWindowTitle("NXGraphScene")
    view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    # create graph scene
    graph = NXGraphModel()
    graph.addNode("N1", outlets=["out"])
    graph.addNode("N2", inlets=["in"])
    graph.addNode("N3", inlets=["in"], outlets=["out"])
    graph.addEdge("N1", "N2", ("out", "in"))
    graphscene = NXGraphScene(graph)
    graphscene.setSceneRect(QRectF(-400, -400, 800, 800))
    view.setScene(graphscene)

    # graphscene.addItem(GraphicsVertexItem("HWELLO"))

    # show window
    view.show()
    sys.exit(app.exec())
