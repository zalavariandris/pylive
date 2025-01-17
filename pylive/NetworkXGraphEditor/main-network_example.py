from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from nx_network_model import NXNetworkModel
from nx_graph_selection_model import NXGraphSelectionModel
from nx_network_scene_outlet_to_inlet import NXNetworkScene
from nx_network_scene_outlet_to_inlet import StandardNetworkDelegte
from nx_node_inspector_view import NXNodeInspectorView

###########
# EXAMPLE #
###########

class NXNetworkExample(QWidget):
    def __init__(self, model:NXNetworkModel, parent: QWidget|None=None) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("NXNetworkExample")

        self._model = model
        self._selection_model = NXGraphSelectionModel(self._model)

        ### create and layout widgets
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        ### graph
        self.graphview = QGraphicsView()
        self.graphview.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.graphview.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
        self.graphview.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.graphview.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.graphview.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        self.graphscene = NXNetworkScene(self._model, self._selection_model, delegate=StandardNetworkDelegte())
        self.graphscene.setSelectionModel(self._selection_model)
        self.graphscene.setSceneRect(-9999,-9999,9999*2,9999*2)
        self.graphview.setScene(self.graphscene)
        self.graphscene.installEventFilter(self)

        ### inspector
        self.function_inspector = NXNodeInspectorView(self._model, self._selection_model)
        self.function_inspector2 = NXNodeInspectorView(self._model, self._selection_model)
        

        ### main splitter
        splitter = QSplitter()
        splitter.addWidget(self.graphview)
        splitter.addWidget(self.function_inspector)
        splitter.addWidget(self.function_inspector2)
        splitter.setSizes([splitter.width()//splitter.count() for idx in range(splitter.count())])
        main_layout.addWidget(splitter)

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # create graph scene
    graph = NXNetworkModel()
    graph.addNode("N1", inlets=["in"], outlets=["out"])
    graph.addNode("N2", inlets=["in"], outlets=["out"])
    graph.addNode("N3", inlets=["in"], outlets=["out"])
    graph.addEdge("N1", "N2", ("out", "in"))

    window = NXNetworkExample(graph)

    # show window
    window.show()
    sys.exit(app.exec())