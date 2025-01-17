from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from bidict import bidict
from python_graph_model import PythonGraphModel
from pylive.NetworkXGraphEditor.nx_graph_selection_model import NXGraphSelectionModel
import inspect

class FunctionInspectorView(QWidget):
    paramTextChanged = Signal(str, str) #parameter name, editor text
    def __init__(self, model:PythonGraphModel, selectionmodel:NXGraphSelectionModel, parent: QWidget | None = None):
        super().__init__(parent=parent)
        ### attributes
        self._model = None
        self._selection_model = None
        self._node_editors: bidict[Hashable, QWidget] = bidict()
        self._attribute_editors: bidict[tuple[Hashable, inspect.Parameter], tuple[QLabel,QWidget]] = bidict()

        ### setup ui
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0,0,0,0)



        # self.header_layout = QVBoxLayout()
        # self.header_layout.setSpacing(0)
        # self.header_layout.setContentsMargins(0,0,0,0)
        # main_layout.addWidget(QLabel("<h4>Node</h4>"))
        # main_layout.addLayout(self.header_layout)

        # self.properties_layout = QFormLayout()
        # self.properties_layout.setSpacing(0)
        # self.properties_layout.setContentsMargins(0,0,0,0)
        
        # main_layout.addLayout(self.properties_layout)

        # self.help_widget = QTextEdit()
        # self.help_widget.setReadOnly(True)
        # main_layout.addWidget(self.help_widget)
        main_layout.addStretch()

        self.setLayout(main_layout)

        ### set models
        self.setModel(model)
        self.setSelectionModel(selectionmodel)

    def setModel(self, model:PythonGraphModel):
        if self._model:
            self._model.nodesChanged.disconnect(self.onNodesChanged)
        if model:
            model.nodesChanged.connect(self.onNodesChanged)
        self._model = model

    def model(self):
        return self._model

    def setSelectionModel(self, selectionmodel:NXGraphSelectionModel):
        if self._selection_model:
            selectionmodel.selectionChanged.disconnect(self.onSelectionChanged)
        if selectionmodel:
            selectionmodel.selectionChanged.connect(self.onSelectionChanged)
        self._selection_model = selectionmodel

    def selectionModel(self):
        return self._selection_model

    def onSelectionChanged(self, selected, deselected):
        assert self._model
        assert self._selection_model

        if node_id := self._selection_model.currentNode():
            node_editor = self.createNodeEditor(self._model, node_id)
            self._node_editors.clear()
            self._node_editors[node_id] = node_editor
            main_layout = cast(QVBoxLayout, self.layout())
            old_item = main_layout.takeAt(0)
            if widget:= old_item.widget():
                widget.deleteLater()


            main_layout.insertWidget(0, node_editor)
            self.updateNodeEditor(self._model, node_id, node_editor)

        # self.updateNodeEditor(self._model, node_id, self.node_editor)

        # def clear_layout_recursive(layout):
        #     while layout.count():
        #         item = layout.takeAt(0)
        #         if item.widget():
        #             item.widget().deleteLater()
        #         elif item.layout():
        #             clear_layout_recursive(item.layout())  # This is actual recursion
        #         del item

        # self._editors.clear()

        # node_id = self._selection_model.currentNode()
        # if node_id:
        #     ### Header
        #     clear_layout_recursive(self.header_layout)
        #     func = self._model.getNodeFunction(node_id)
        #     import inspect
        #     if module:=inspect.getmodule(func):
        #         module_label = Q.label(f"{module.__name__}")
        #     else:
        #         module_label = Q.label(f"cant find module for fn: {func}")
        #     kind_label = Q.label(f"{func.__class__.__name__}")
        #     name_label = Q.label(f"{func.__qualname__}")

        #     self.header_layout.addWidget(module_label)
        #     self.header_layout.addWidget(kind_label)
        #     self.header_layout.addWidget(name_label)

        #     ### properties
        #     clear_layout_recursive(self.properties_layout)
        #     for param in inspect.signature(func).parameters.values():
        #         label, widget = self.createAttributeEditor(self._model, (node_id, param))
        #         self._editors[(node_id, param)] = (label, widget)

        #     ### help
        #     import pydoc
        #     import html
        #     doc = pydoc.render_doc(func)
        #     self.help_widget.setPlainText(doc)
        # else:
        #     clear_layout_recursive(self.header_layout)
        #     clear_layout_recursive(self.properties_layout)

    def onNodesChanged(self, changes:dict[Hashable, list[str]]):
        assert self._model is not None
        assert self._selection_model is not None

        node_id = self._selection_model.currentNode()    
        if node_id and node_id in changes:
            func = self._model.getNodeFunction(node_id)
            for prop in changes[node_id]:
                param = inspect.signature(func).parameters[prop]
                try:
                    value = self._model.getNodeProperty(node_id, prop)
                    
                    """prop exist"""
                    try:
                        # get the editor
                        editor = self._attribute_editors[(node_id, param)]
                    except KeyError:
                        # no editor exist for the property yet
                        # create the editor
                        if editor := self.createAttributeEditor(self._model, (node_id, param) ):
                            self._attribute_editors[(node_id, param)] = editor
                            

                    if editor:
                        # update editor if exists
                        self.updateAttributeEditor(self._model, (node_id, param), editor)

                except KeyError:
                    """prop does not exist"""
                    try:
                        """delete editor if exist"""
                        label, widget = self._attribute_editors[(node_id, param)]
                        del self._attribute_editors[(node_id, param)]
                        label.deleteLater()
                        widget.deleteLater()
                    except KeyError:
                        pass

    ### Delegate methods
    def createNodeEditor(self, model:PythonGraphModel, node_id:Hashable)->QWidget:
        node_editor = QWidget()
        editor_layout = QVBoxLayout()
        node_editor.setLayout(editor_layout)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(0)
        header_layout.setContentsMargins(0,0,0,0)

        header_label = QLabel("Header")
        header_layout.addWidget(header_label)

        properties_layout = QFormLayout()
        properties_layout.setSpacing(0)
        properties_layout.setContentsMargins(0,0,0,0)

        editor_layout.addLayout(header_layout)
        editor_layout.addLayout(properties_layout)

        for arg in model.arguments(node_id):
            if attribute_editor := self.createAttributeEditor(model, (node_id, arg)):
                self._attribute_editors[(node_id, arg)] = attribute_editor

        return node_editor

    def updateNodeEditor(self, model:PythonGraphModel, node_id:Hashable, editor:QWidget)->None:
        editor_layout = cast(QVBoxLayout, editor.layout())

        ### header
        header_layout = cast(QVBoxLayout, editor_layout.itemAt(0))
        header_label = cast(QLabel, header_layout.itemAt(0).widget())

        func = model.getNodeFunction(node_id)
        print(func)
        header_label.setText(f"""\
        <h1>id: {node_id}</h1>
        <em>func: {func!s}</em>
        <p>module: {inspect.getmodule(func)}</p>""")

    def itemEditor(self, key):
        return self._editors[key]

    def createAttributeEditor(self, model:PythonGraphModel, item:tuple[Hashable, inspect.Parameter] )->tuple[QLabel, QWidget]:
        assert self._model
        assert self._selection_model
        node_id, param = item

        label = QLabel(param.name)
        lineedit = QLineEdit()
        try:
            lineedit.setText(f"{model.getNodeProperty(node_id, param.name)!r}")
        except:
            value = ""
        lineedit.setPlaceholderText(f"{param.default!r}" if param.default is not inspect.Parameter.empty else "")

        lineedit.textChanged.connect(
            lambda text, model=self._model, node_id=self._selection_model.currentNode(), prop=param, editor=(label, lineedit):
            self.updateAttributeModel(model, (node_id, param), editor))

        node_editor = cast(QWidget, self.itemEditor(item))
        node_editor_layout = cast(QVBoxLayout, node_editor.layout())
        node_editor_layout = cast(QVBoxLayout, node_editor.layout())
        properties_layout = cast(QFormLayout, node_editor_layout.itemAt(1))
        properties_layout.addRow(label, lineedit)
        return label, lineedit

    def updateAttributeEditor(self, model, item:tuple[Hashable, inspect.Parameter], editor:tuple[QLabel, QWidget])->None:
        label, lineedit = cast(tuple[QLabel, QLineEdit], editor)
        node_id, param = item
        lineedit.setText(model.getNodeProperty(node_id, param.name))

    def updateAttributeModel(self, model, item:tuple[Hashable, inspect.Parameter], editor:tuple[QLabel, QWidget])->None:
        label, lineedit = cast(tuple[QLabel, QLineEdit], editor)
        node_id, param = item
        model.updateNodeProperties(node_id, **{param.name: lineedit.text()})