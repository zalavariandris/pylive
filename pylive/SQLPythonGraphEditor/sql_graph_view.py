from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


from sql_graph_model import SQLGraphModel



class SQLGraphScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self._model: SQLGraphModel|None = None

    def setModel(self, model:SQLGraphModel):
        if self._model:
            self._model.nodes.rowsInserted.disconnect(self.onNodesInserted)
            self._model.nodes.rowsAboutToBeRemoved.disconnect(self.onNodesRemoved)
            self._model.edges.rowsInserted.disconnect(self.onEdgesInserted)
            self._model.edges.rowsAboutToBeRemoved.disconnect(self.onEdgesRemoved)

        if model:
            print("listen to model changes")
            model.nodes.rowsInserted.connect(self.onNodesInserted)
            model.nodes.rowsAboutToBeRemoved.connect(self.onNodesRemoved)
            model.edges.rowsInserted.connect(self.onNodesInserted)
            model.edges.rowsAboutToBeRemoved.connect(self.onNodesRemoved)

        self._model = model

    def onNodesInserted(self, parent: QModelIndex, first: int, last: int):
        assert self._model
        """Add a QGraphicsObject for each inserted node."""
        print("onNodesInserted", first, last)
        for row in range(first, last + 1):
            # Retrieve the node data from the model
            index = self._model.nodes.index(row, 0, parent)
            node_data = self._model.nodes.data(index)


            print("add node", node_data)
            # # Create a QGraphicsObject for the node
            # graphics_object = self._delegate.createNodeEditor()

            # # Add the QGraphicsObject to the scene
            # self.addItem(graphics_object)

    def onNodesRemoved(self):
        print("nodes inserted")
        ...

    def onEdgesInserted(self):
        """add a QGraphicsObject for each inserted node"""
        ...

    def onEdgesRemoved(self):
        ...