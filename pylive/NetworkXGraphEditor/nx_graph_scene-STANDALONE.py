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
    VertexShape,
    LinkShape,
    PortShape,
)


##############
# GRAPHSCENE #
##############

from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel

from dataclasses import dataclass

type NodeId = Hashable
type LinkId = tuple[NodeId, NodeId, Hashable]


class NXGraphScene(QGraphicsScene):
    def __init__(self, model: NXGraphModel):
        super().__init__()
        self._model: NXGraphModel = model
        self._node_graphics_objects: dict[NodeId, VertexGraphicsObject] = dict()
        self._link_graphics_objects: dict[LinkId, LinkGraphicsObject] = dict()
        self._draft_link: LinkGraphicsObject | None = None

        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        _ = self._model.nodesAdded.connect(
            lambda nodes: [self.onNodeCreated(n) for n in nodes]
        )
        _ = self._model.nodesAboutToBeRemoved.connect(
            lambda nodes: [self.onNodeDeleted(n) for n in nodes]
        )
        _ = self._model.edgesAdded.connect(
            lambda edges: [self.onLinkCreated(e) for e in edges]
        )
        _ = self._model.edgesAboutToBeRemoved.connect(
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
            self.onLinkCreated(e)

    def linkGraphicsObject(self, e: LinkId) -> "LinkGraphicsObject":
        return self._link_graphics_objects[e]

    def nodeGraphicsObject(self, n: NodeId) -> "VertexGraphicsObject":
        return self._node_graphics_objects[n]

    def sourceGraphicsObject(self, e: LinkId) -> QGraphicsItem:
        u, v, k = e
        return self.nodeGraphicsObject(u)

    def targetGraphicsObject(self, e: LinkId) -> QGraphicsItem:
        u, v, k = e
        return self.nodeGraphicsObject(u)

    def updateAttachedNodes(self, e: LinkId, kind: Literal["in", "out"]):
        u, v, k = e
        match kind:
            case "in":
                if node := self._node_graphics_objects.get(u, None):
                    node.update()
            case "out":
                if node := self._node_graphics_objects.get(v, None):
                    node.update()

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

        u, v, k = e
        link.move(self.sourceGraphicsObject(e), self.targetGraphicsObject(e))

        self.updateAttachedNodes(e, "in")
        self.updateAttachedNodes(e, "out")

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
        self._node_graphics_objects[n] = VertexGraphicsObject(n)
        self.addItem(self.nodeGraphicsObject(n))

    def onNodeDeleted(self, n: NodeId):
        if n in self._node_graphics_objects:
            node_graphics_object = self.nodeGraphicsObject(n)
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

    def nodeAt(self, position: QPointF) -> "VertexGraphicsObject":
        return cast(
            VertexGraphicsObject,
            self._findGraphItemAt(VertexGraphicsObject, position),
        )

    def linkAt(self, position: QPointF) -> "LinkGraphicsObject":
        return cast(
            LinkGraphicsObject,
            self._findGraphItemAt(LinkGraphicsObject, position),
        )

    def layout(self):
        from pylive.utils.graph_layout import hiearchical_layout_with_nx

        pos = hiearchical_layout_with_nx(self._model.G, scale=100)
        for N, (x, y) in pos.items():
            widget = self.nodeGraphicsObject(N)
            widget.setPos(x, y)


###########################
# Active Graphics Objects #
###########################


class VertexGraphicsObject(VertexShape):
    def __init__(
        self,
        n: NodeId,
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(
            title=f"'{n}'",
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
            u, v, k = e
            self.graphscene()
            source = self.graphscene().nodeGraphicsObject(u)
            target = self.graphscene().nodeGraphicsObject(v)
            edge = self.graphscene().linkGraphicsObject(e)
            edge.move(source, target)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.isSelected():
            super().mousePressEvent(event)
        else:
            self.graphscene().makeDraftLink()
            self.grabMouse()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.isSelected():
            super().mouseMoveEvent(event)
        else:
            draft = self.graphscene().draft
            assert draft is not None

            if node := self.graphscene().nodeAt(event.scenePos()):
                draft.move(self, node)
            else:
                draft.move(self, event.scenePos())

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.isSelected():
            super().mouseReleaseEvent(event)
        else:
            self.ungrabMouse()
            self.graphscene().resetDraftLink()

            if target := self.graphscene().nodeAt(event.scenePos()):
                scene = self.graphscene()
                scene._model.addEdge(self._n, target._n)

            return super().mouseReleaseEvent(event)


class LinkGraphicsObject(LinkShape):
    def __init__(self, e: LinkId, parent: QGraphicsItem | None = None):
        u, v, k = e
        super().__init__(label=f"{k}", parent=parent)
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
    view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
    view.setWindowTitle("NXGraphScene")
    view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    # create graph scene
    graph = NXGraphModel()
    graph.addNode("N1")
    graph.addNode("N2")
    graph.addNode("N3")
    graph.addEdge("N1", "N2")
    graphscene = NXGraphScene(graph)
    graphscene.setSceneRect(QRectF(-400, -400, 800, 800))
    view.setScene(graphscene)

    # graphscene.addItem(GraphicsVertexItem("HWELLO"))

    # show window
    view.show()
    sys.exit(app.exec())
