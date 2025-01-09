from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel
from pylive.NetworkXGraphEditor.nx_network_scene import (
    NXNetworkScene,
    NodeGraphicsObject,
    LinkGraphicsObject,
    InletGraphicsObject,
    NodeId,
    OutletGraphicsObject,
    LinkId,
    InletId,
    OutletId,
    NodeId,
)


class MyVertexGraphicsObject(NodeGraphicsObject):
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


class MyGraphScene(NXNetworkScene):
    def onNodeCreated(self, n: NodeId):
        # inlet = InletGraphicsObject(InletId(n, "in"))
        # outlet = OutletGraphicsObject(OutletId(n, "out"))
        node = MyVertexGraphicsObject(n, inlets=[], outlets=[])

        self._node_graphics_objects[n] = node
        self._target_graphics_objects[n] = node
        self._source_graphics_objects[n] = node

        self.addItem(self.nodeGraphicsObject(n))

    def onLinkCreated(self, e: LinkId):
        link = LinkGraphicsObject(e)
        self._link_graphics_objects[e] = link
        self.addItem(link)

        link.move(self.sourceGraphicsObject(e), self.targetGraphicsObject(e))

        self.updateAttachedSource(e)
        self.updateAttachedTarget(e)

    def sourceGraphicsObject(self, e: LinkId) -> QGraphicsItem:
        u, v, k = e
        return self._source_graphics_objects[u]

    def targetGraphicsObject(self, e: LinkId) -> QGraphicsItem:
        u, v, k = e
        return self._target_graphics_objects[v]


###########
# EXAMPLE #
###########
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # setup main window
    view = QGraphicsView()
    view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
    view.setWindowTitle("MyGraphScene")
    view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    # create graph scene
    graph = NXGraphModel()
    graph.addNode("N1")
    graph.addNode("N2")
    graph.addNode("N3")
    graph.addEdge("N1", "N2", 10)
    graphscene = MyGraphScene(graph)
    graphscene.setSceneRect(QRectF(-400, -400, 800, 800))
    view.setScene(graphscene)

    # graphscene.addItem(GraphicsVertexItem("HWELLO"))

    # show window
    view.show()
    sys.exit(app.exec())
