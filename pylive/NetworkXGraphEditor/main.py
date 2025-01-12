from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from nx_graph_model import NXGraphModel
from nx_graph_selection_model import NXGraphSelectionModel
from nx_network_scene import NXNetworkScene
from nx_inspector_view import NXInspectorView
from pylive.QtTerminal.terminal_with_exec import Terminal


class GraphEditorWindow(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("NXNetworkScene")

        ### model
        self.model = NXGraphModel()
        self.selectionmodel = NXGraphSelectionModel(self.model)

        ### widgets
        # graphview
        self.graphview = QGraphicsView()
        self.graphview.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.graphview.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.graphview.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.graphview.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform, True
        )

        graphscene = NXNetworkScene(self.model, self.selectionmodel)
        graphscene.setSceneRect(QRectF(-400, -400, 800, 800))
        self.graphview.setScene(graphscene)

        # inspector
        self.inspector = NXInspectorView()
        self.inspector.setModel(self.model)
        self.inspector.setSelectionModel(self.selectionmodel)

        # terminal
        self.terminal = Terminal()
        self.terminal.setContext({"app": self})

        ### Layout
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter()
        mainLayout.addWidget(splitter)
        splitter.addWidget(self.graphview)
        splitter.addWidget(self.inspector)
        splitter.addWidget(self.terminal)
        # splitter.addWidget(self.nodelistview)
        splitter.setSizes(
            [
                splitter.width() // splitter.count()
                for _ in range(splitter.count())
            ]
        )
        self.setLayout(mainLayout)

        # example scene

        self.model.addNode("N1", outlets=["out"])
        self.model.addNode("N2", inlets=["in"])
        self.model.addNode("N3", inlets=["in"], outlets=["out"])
        self.model.addEdge("N1", "N2", ("out", "in"))
        graphscene.layout()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    window = NetworkEditorWindow()

    # show window
    window.show()
    sys.exit(app.exec())
