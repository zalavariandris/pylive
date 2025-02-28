from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import pylive.utils.qtfactory as qf
# import qt_parameters

from pylive.VisualCode_v4.py_data_model import PyDataModel
from pylive.VisualCode_v4.py_proxy_model import PyProxyParameterModel
from pylive.QtScriptEditor.script_edit import ScriptEdit

class PyInspectorView(QFrame):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._model:PyDataModel|None=None
        self._current_node:str|None=None
        self._parameter_model: PyProxyParameterModel|None=None
        self._model_connections = []
        self._view_connections = []
        self.setupUI()

    def showEvent(self, event: QShowEvent) -> None:
        for signal, slot in self._model_connections:
            signal.connect(slot)
        for signal, slot in self._view_connections:
            signal.connect(slot)

        return super().showEvent(event)

    def hideEvent(self, event: QHideEvent) -> None:
        print("hideEvent")
        for signal, slot in self._model_connections:
            signal.disconnect(slot)
        for signal, slot in self._view_connections:
            signal.disconnect(slot)

    def setupUI(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)  # Styled panel for the frame
        self.setFrameShadow(QFrame.Shadow.Raised)

        self.name_label = QLabel()

        self.parameter_table_editor = QTableView()  
        self.parameter_table_editor.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.parameter_table_editor.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.parameter_table_editor.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.parameter_table_editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.parameter_table_editor.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)

        self.source_editor = ScriptEdit()
        self.source_editor.setPlaceholderText("source...")

        main_layout = qf.vboxlayout([
            self.name_label,
            QLabel("<h2>Parameters</h2>"),
            self.parameter_table_editor,
            QLabel("<h2>Source</h2>"),
            self.source_editor
        ])

        self.setLayout(main_layout)

        # bind view to model
        self._view_connections = [
            (self.source_editor.textChanged, lambda: self._syncModelData('source'))
        ]
        for signal, slot in self._view_connections:
            signal.connect(slot)
        
    def setModel(self, model: PyDataModel|None):
        if self._model:
            for signal, slot in self._model_connections:
                signal.disconnect(slot)

            self._parameter_model = None

        if model:
            self._model_connections = [
                (model.sourceChanged, lambda: self._syncEditorData(attr='source'))
            ]
            for signal, slot in self._model_connections:
                signal.connect(slot)

            self._parameter_model = PyProxyParameterModel(model)


        self._model = model
        self.parameter_table_editor.setModel(self._parameter_model)
        if self._parameter_model:
            self._parameter_model.setNode(self._current_node)

    def _syncEditorData(self, attr:Literal['name', 'source']):
        if not self._model or not self._current_node:
            self.name_label.setText("<h1>- no selection -</h1>")
            self.source_editor.setPlainText('')
            return

        match attr:
            case 'name':
                pretty_name = self._current_node or '- no selection -'
                pretty_name = pretty_name.replace("_", " ").title()
                self.name_label.setText(f"<h1>{pretty_name}<h1>")
            case 'source':
                value = self._model.nodeSource(self._current_node)
                if value != self.source_editor.toPlainText():
                    self.source_editor.setPlainText(value)

    def _syncModelData(self, attr='source'):
        if not self._model or not self._current_node:
            return

        match attr:
            case 'source':
                self._model.setNodeSource(self._current_node, self.source_editor.toPlainText())

    def setCurrent(self, node:str|None):
        self._current_node = node

        self._syncEditorData('name')
        self._syncEditorData('source')
        if self._parameter_model:
            self._parameter_model.setNode(node)