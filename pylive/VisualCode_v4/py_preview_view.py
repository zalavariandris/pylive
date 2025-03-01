from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pylive.VisualCode_v4.py_data_model import PyDataModel


class PyPreviewView(QFrame):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._model:PyDataModel|None=None
        self._current_node:str|None = None

        self._model_connections = []
        self._view_connections = []
        self.setupUI()

    def setupUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

    def setModel(self, model: PyDataModel|None):
        if self._model:
            for signal, slot in self._model_connections:
                signal.disconnect(slot)

            self._parameter_model = None

        if model:
            self._model_connections = [
                (model.resultChanged, self._onResultChanged)
            ]
            for signal, slot in self._model_connections:
                signal.connect(slot)

        self._model = model

    def display(self, data:Any):
        layout = cast(QVBoxLayout, self.layout())

        for i in reversed(range(layout.count())):
            item=layout.takeAt(i)
            if widget:=item.widget():
                widget.deleteLater()

        match data:
            case Exception():
                import traceback
                error_text = ''.join(traceback.TracebackException.from_exception(data).format())
                label = QLabel()
                label.setWordWrap(True)
                label.setText(f"<p style='white-space:pre; color: red'>{error_text}<p>")
                layout.addWidget(label)
            case QWidget():
                layout.addWidget(data)
            case _:
                label = QLabel()
                label.setWordWrap(True)
                label.setText(f"<p style='white-space:pre'>{data}<p>")
                layout.addWidget(label)

    def _onResultChanged(self, node):
        print(f"PyPreviewView->_onResultChanged {node}, {self._current_node}")
        if node == self._current_node:
            self._syncEditorData()

    def _syncEditorData(self, hint=None):
        print(f"PyPreviewView->_syncEditorData")
        if not self._model:
            return

        if self._current_node:
            result = self._model.result(self._current_node)
            error = self._model.error(self._current_node)

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