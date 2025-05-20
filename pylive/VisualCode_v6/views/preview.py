from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from pylive.VisualCode_v6.py_graph_model import PyGraphModel
from pylive.VisualCode_v6.py_proxy_node_model import PyProxyNodeModel
from pylive.VisualCode_v6.py_proxy_link_model import PyProxyLinkModel


class PreView(QScrollArea):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter)
        self.setWidgetResizable(True)
        self._previous_parent:QObject|None = None

        self.preview_label = QLabel()
        self.setWidget(self.preview_label)

        self._model:PyGraphModel|None=None
        self.node_proxy_model:PyProxyNodeModel|None = None
        self.node_selection_model:QItemSelectionModel|None=None
        self._current:str|None=None
        self._model_connections = []
        self._selection_connections = []
        
    def setModel(self, model:PyGraphModel|None):
        if self._model:
            for signal, slot in self._model_connections:
                signal.disconnect(slot)

        if model:
            self._model_connections = [
                (model.dataChanged, 
                    lambda nodes, hints: self._setEditorData(hints) 
                    if self._current in nodes
                    else 
                    None),
            ]
            for signal, slot in self._model_connections:
                signal.connect(slot)
        self._model = model

    def setSelectionModel(self, selection:QItemSelectionModel|None, proxy:PyProxyNodeModel|None):
        assert all([selection is None, proxy is None]) or all([selection is not None, proxy is not None])
        
        if self.node_proxy_model and self.node_selection_model:
            for signal, slot in self._selection_connections:
                signal.disconnect(slot)

        if selection and proxy:
            self._selection_connections = [
                (selection.currentChanged, 
                    lambda current, previous: self._setCurrent(proxy.mapToSource(current)))
            ]

            for signal, slot in self._selection_connections:
                signal.connect(slot)

        self.node_proxy_model = proxy
        self.node_selection_model = selection

    def _setCurrent(self, node:str|None):
        self._current = node
            
        if node:
            self._setEditorData()
        else:
            self._clearEditorData()

    def _setEditorData(self, hints:list=[]):
        assert self._model
        assert self._current
        ### Previews
        if 'result' in hints or not hints:
            error, result = self._model.data(self._current, 'result')

            if error:
                self.preview_label.setText(f"{error}")
            else:
                match result:
                    case QWidget():
                        raise NotImplementedError("QWidgets are not yet supported")
                    case _:
                        self.preview_label.setText(f"{result}")

    def _clearEditorData(self):
        self.preview_label.setText("")
