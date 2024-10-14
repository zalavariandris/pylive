from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from Panel import Panel
from typing import List, Tuple
from pathlib import Path
from GraphModel import GraphModel

class GraphRunner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setLayout(QVBoxLayout())
        self.title_label = QLabel()
        self.content_frame = QTextEdit()
        self.layout().addWidget(self.title_label)
        self.layout().addWidget(self.content_frame)

        toolbar = QToolBar()
        toolbar.addAction(QAction("restart", self))

        self.layout().setMenuBar(toolbar)

        self.model = None
        self.selectionmodel = None

        self.logs = ""

    def setModel(self, graphmodel:GraphModel):
        self.model = graphmodel

        self.model.nodesInserted.connect(self.run)
        self.model.nodesRemoved.connect(self.run)
        self.model.nodeChanged.connect(self.run)


        self.model.inletChanged.connect(self.run)
        self.model.outletChanged.connect(self.run)

        self.model.edgesInserted.connect(self.run)
        self.model.edgesRemoved.connect(self.run)
        self.model.edgeChanged.connect(self.run)

        self.run()

    def setSelectionModel(self, node_selectionmodel):
        self.selectionmodel = node_selectionmodel

        @self.selectionmodel.currentRowChanged.connect
        def currentRowChanged(current: QModelIndex, previous: QModelIndex):
            self.run()

        @self.selectionmodel.selectionChanged.connect
        def selectionChanged(selected:List[QModelIndex], deselected:List[QModelIndex]):
            self.run()

    def log(self, text="", end="\n"):
        self.logs+=f"{text}{end}"

        self.content_frame.setPlainText(self.logs)

    def clear(self):
        self.logs = ""
        self.content_frame.setPlainText(self.logs)


    @Slot()
    def run(self):
        self.clear()
        
        if self.selectionmodel and self.selectionmodel.hasSelection():
            node = self.selectionmodel.currentIndex()
            self.log(f"{node.siblingAtColumn(1).data()} {node.data()}")
            self.log("Inlets")
            for inlet in self.model.findInlets(node):
                self.log(f"- {inlet.siblingAtColumn(2).data()}, {inlet.data()}")
            self.log("Outlets")
            for outlet in self.model.findOutlets(node):
                self.log(f"- {outlet.siblingAtColumn(2).data()}, {outlet.data()}")
            self.log()
            self.log("Source nodes")
            for source in self.model.findConnectedNodes(node, direction="SOURCE"):
                self.log(f"- {source.siblingAtColumn(1).data()}, {source.data()}")
            self.log()
            self.log("Target nodes")
            for source in self.model.findConnectedNodes(node, direction="TARGET"):
                self.log(f"- {source.siblingAtColumn(1).data()}, {source.data()}")

        else:
            self.log("# Root Nodes")
            for node in self.model.rootRodes():
                self.log(f"- {node.siblingAtColumn(1).data()} {node.data()}")
            self.log()
            self.log("# DFS")
            self.log("## roots")
            for node in self.model.rootRodes():
                self.log(node.data())
            self.log("## path")
            for node in reversed(list(self.model.dfs())):
                self.log(node.data())

