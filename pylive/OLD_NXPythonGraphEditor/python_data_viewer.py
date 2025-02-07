from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from parso.python.tree import Keyword

from python_graph_model import PythonGraphModel
from pylive.NetworkXGraphEditor.nx_graph_selection_model import NXGraphSelectionModel
from python_graph_model import PythonGraphModel


class PythonDataViewer(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._model:PythonGraphModel|None = None
        self._selection_model:NXGraphSelectionModel|None = None

        main_layout = QVBoxLayout()
        self._label = QLabel()
        self._label.setWordWrap(True)
        main_layout.addWidget(self._label)
        self.setLayout(main_layout)

    def setModel(self, model:PythonGraphModel):
        if self._model:
            self._model.nodeAttributesAdded.disconnect(self.onNodeAttributesAdded)
            self._model.nodeAttributesChanged.disconnect(self.onNodeAttributesChanged)
            self._model.nodeAttributesRemoved.disconnect(self.onNodeAttributesRemoved)
        if model:
            model.nodeAttributesAdded.connect(self.onNodeAttributesAdded)
            model.nodeAttributesChanged.connect(self.onNodeAttributesChanged)
            model.nodeAttributesRemoved.connect(self.onNodeAttributesRemoved)
        self._model = model

    def setSelectionModel(self, selection_model:NXGraphSelectionModel):
        if self._selection_model:
            self._selection_model.selectionChanged.disconnect(self.onSelectionChanged)

        if selection_model:
            selection_model.selectionChanged.connect(self.onSelectionChanged)

        self._selection_model = selection_model

    def onSelectionChanged(self, selected, deselected):
        self.preview()

    def onNodeAttributesAdded(self, node_attributes:dict[Hashable, list[str]]):
        assert self._model
        assert self._selection_model
        current_node_id = self._selection_model.currentNode()
        if current_node_id in node_attributes:
            self.preview()

    def onNodeAttributesChanged(self, node_attributes:dict[Hashable, list[str]]):
        assert self._model
        assert self._selection_model
        current_node_id = self._selection_model.currentNode()
        if current_node_id in node_attributes:
            self.preview()
        
    def onNodeAttributesRemoved(self, node_attributes:dict[Hashable, list[str]]):
        assert self._model
        assert self._selection_model
        current_node_id = self._selection_model.currentNode()
        if current_node_id in node_attributes:
            self.preview()

    def preview(self):
        assert self._model
        assert self._selection_model

        current_node_id = self._selection_model.currentNode()
        try:
            cache = self._model.cache(current_node_id)
            self._label.setText(f"'{cache!r}'")
        except KeyError:
            try:
                error = self._model.error(current_node_id)
                self._label.setText(f"'{error!r}'")
            except KeyError:
                self._label.setText("no results")