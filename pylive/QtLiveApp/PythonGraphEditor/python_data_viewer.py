from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from python_graph_model import PythonGraphModel
from pylive.NetworkXGraphEditor.nx_graph_selection_model import NXGraphSelectionModel

class PythonDataViewer(QWidget):
    def __init__(self, model:PythonGraphModel, selectionmodel:NXGraphSelectionModel, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._model = None
        self._selection_model = None

        main_layout = QVBoxLayout()
        self._label = QLabel()
        self._label.setWordWrap(True)
        main_layout.addWidget(self._label)
        self.setLayout(main_layout)

        self.setModel(model)
        self.setSelectionModel(selectionmodel)

    def setModel(self, model:PythonGraphModel):
        if model:
            @model.nodesChanged.connect
            def _(changes):
                assert self._selection_model
                if current_node_id:=self._selection_model.currentNode():
                    if current_node_id in changes.keys():
                        self.showNode(current_node_id)
        self._model = model

    def model(self):
        return self._model

    def setSelectionModel(self, selectionmodel:NXGraphSelectionModel):
        if selectionmodel:
            @selectionmodel.selectionChanged.connect
            def _(selected, deselected):
                assert self._selection_model
                self.showNode(self._selection_model.currentNode())

        self._selection_model = selectionmodel

    def selectionModel(self):
        return self._selection_model

    @Slot()
    def showNode(self, node_id:Hashable|None):
        assert self._model
        assert self._selection_model

        if node_id := self._selection_model.currentNode():
            try:
                result = self._model.getNodeResult(node_id)
                match result:
                    case list():
                        self._label.setText(f"{result}")
                    case _:
                        self._label.setText(f"{result}")
            except Exception as err:
                self._label.setText(f"{err}")
        else:
            self._label.setText(f"-no selection-")
