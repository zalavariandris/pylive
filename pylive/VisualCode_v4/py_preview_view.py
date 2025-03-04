from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pylive.VisualCode_v4.py_data_model import PyDataModel


class PyPreviewView(QScrollArea):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._model:PyDataModel|None=None
        self._current_node:str|None = None

        self.setBackgroundRole(QPalette.ColorRole.Accent)

        self._model_connections = []
        self._view_connections = []

    def setModel(self, model: PyDataModel|None):
        if self._model:
            for signal, slot in self._model_connections:
                signal.disconnect(slot)

            self._parameter_model = None

        if model:
            self._model_connections = [
                (model.resultInvaliadated, self._onResultInvalidated)
            ]
            for signal, slot in self._model_connections:
                signal.connect(slot)

        self._model = model

    def display(self, data:Any):
        match data:
            case Exception():
                import traceback
                error_text = ''.join(traceback.TracebackException.from_exception(data).format())
                label = QLabel()
                label.setWordWrap(True)
                label.setText(f"<p style='white-space:pre; color: red'>{error_text}<p>")
                self.setWidget(label)
            case _:
                label = QLabel()
                label.setWordWrap(True)
                label.setText(f"<p style='white-space:pre'>{data}<p>")
                self.setWidget(label)

    def _onResultInvalidated(self, node):
        print(f"PyPreviewView->_onResultChanged {node}, {self._current_node}")
        if node == self._current_node:
            self._syncEditorData()

    def _syncEditorData(self, hint=None):
        print(f"PyPreviewView->_syncEditorData")
        if not self._model:
            return

        if self._current_node:
            error, result = self._model.result(self._current_node)

            if error:
                self.display(error)
            else:
                self.display(result)
        else:
            self.display("- no selection -")

    def setCurrent(self, node:str|None):
        print(f"PyPreviewView->setCurrent {node}")
        if node != self._current_node:
            self._current_node = node
            self._syncEditorData()