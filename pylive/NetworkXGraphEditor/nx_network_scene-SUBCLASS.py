from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.NetworkXGraphEditor.nx_graph_shapes import NodeShape, LinkShape

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

    def onLinkCreated(self, e: LinkId):
        link = LinkGraphicsObject(e)
        self._link_graphics_objects[e] = link
        self.addItem(link)

        u, v, (o, i) = e
        link.move(
            self.outletGraphicsObject(OutletId(u, o)),
            self.inletGraphicsObject(InletId(v, i)),
        )


###########
# EXAMPLE #
###########
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # setup main window
    view = QGraphicsView()
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
