from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from networkx import node_boundary
from networkx.generators import line
from numpy import isin
from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel
from pylive.NetworkXGraphEditor.nx_graph_selection_model import (
    NXGraphSelectionModel,
)
from pylive.NetworkXGraphEditor.nx_graph_shapes import BaseNodeItem
from pylive.utils.unique import make_unique_name
from pylive.utils.qt import signalsBlocked

from bidict import bidict

type AttrId=str

class NXNodeInspectorDelegate(QObject):
    def createNodeEditor(self, model, node_id)->QWidget:
        node_editor = QWidget()
        node_editor_layout = QVBoxLayout()
        node_editor.setLayout(node_editor_layout)

        ### header
        header_label = QLabel("<h1>None</h1>")
        node_editor_layout.addWidget(header_label)

        ### attributes
        new_attribute_edit = QLineEdit()
        new_attribute_edit.setPlaceholderText("new attribute")
        node_editor_layout.addWidget(new_attribute_edit)

        @new_attribute_edit.returnPressed.connect
        def _add_attribute_to_current_node(model=model, node_id=node_id):
            attr = new_attribute_edit.text()
            model.updateNodeAttributes(node_id, **{attr: None})
            new_attribute_edit.clear()

        attributes_layout = QFormLayout()
        node_editor_layout.addLayout(attributes_layout)

        return node_editor

    def updateNodeEditor(self, model, node_id, node_editor):
        header_label = node_editor.layout().itemAt(0).widget()
        header_label.setText(f"""\
            <h1>{node_id}</h1>""")

    def createAttributeEditor(self, parent_node_editor, model, node_id, attr:str):
        attr_widget = QLineEdit()

        @attr_widget.textChanged.connect
        def _update_model(text, model=model, node_id=node_id, attr=attr):
            assert model
            model.updateNodeAttributes(node_id, **{attr: text})

        label_widget = self.createAttributeLabel(model, node_id, attr)
        attributes_layout = parent_node_editor.layout().itemAt(2).layout()
        attributes_layout.addRow(label_widget, attr_widget)

        return attr_widget

    def deleteAttributeEditor(self, parent_node_editor, attr_widget):
        attributes_layout = parent_node_editor.layout().itemAt(2).layout()
        attributes_layout.removeRow(attr_widget)

    def createAttributeLabel(self, model, node_id, attr:str):
        # create attribute label
        label_text = QLabel(attr)
        remove_btn = QPushButton("x")
        remove_btn.setFixedSize(22, 22)
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(0,0,0,0)
        label_layout.setSpacing(0)
        label_widget = QWidget()
        label_widget.setLayout(label_layout)
        label_layout.addWidget(remove_btn)
        label_layout.addWidget(label_text)
        
        @remove_btn.pressed.connect
        def _(model=model, node_id=node_id, attr=attr):
            model.deleteNodeAttribute(node_id, attr)

        return label_widget

    def updateAttributeEditor(self, model, node_id, attr, attr_widget):
        value = model.getNodeAttribute(node_id, attr)
        if f"{value}" != attr_widget.text():
            attr_widget.setText(f"{value}")


class NXNodeInspectorView(QWidget):
    def __init__(self, 
        model:NXGraphModel, 
        selection:NXGraphSelectionModel, 
        delegate=NXNodeInspectorDelegate(), 
        parent: QWidget | None = None
    ):
        self._model: NXGraphModel | None = None
        self._selection_model: NXGraphSelectionModel | None = None
        self._delegate = delegate
        self._node_editor:QWidget|None=None
        self._attribute_editors: bidict[AttrId, QLineEdit] = bidict()
        super().__init__(parent=parent)

        # Setup UI
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addStretch()

        #
        self.setModel(model)
        self.setSelectionModel(selection)

    def setModel(self, model: NXGraphModel):
        if self._model:
            model.nodeAttributesAdded.disconnect(self.onNodeAttributesAdded)
            model.nodeAttributesAboutToBeRemoved.disconnect(self.onNodeAttributesRemoved)
            model.nodeAttributesChanged.disconnect(self.onNodeAttributesChanged)
        if model:
            model.nodeAttributesAdded.connect(self.onNodeAttributesAdded)
            model.nodeAttributesAboutToBeRemoved.connect(self.onNodeAttributesRemoved)
            model.nodeAttributesChanged.connect(self.onNodeAttributesChanged)
        self._model = model

    def setSelectionModel(self, selection_model: NXGraphSelectionModel):
        if self._selection_model:
            selection_model.selectionChanged.disconnect(self.onSelectionChanged)
        if selection_model:
            selection_model.selectionChanged.connect(self.onSelectionChanged)
        
        self._selection_model = selection_model

    def onSelectionChanged(self, selected, deselected):
        assert self._model
        assert self._selection_model

        ### create node editor
        main_layout = cast(QVBoxLayout, self.layout())

        if item:=main_layout.takeAt(0):
            if widget:=item.widget():
                widget.deleteLater()

        if node_id:=self._selection_model.currentNode():
            self._node_editor = self._delegate.createNodeEditor(self._model, node_id)
            self._delegate.updateNodeEditor(self._model, node_id, self._node_editor)
            main_layout.insertWidget(0, self._node_editor)
            self.onNodeAttributesAdded({node_id: self._model.nodeAttributes(node_id)})

    def onNodeAttributesAdded(self, node_attributes:dict[Hashable, Iterable[AttrId]]):
        assert self._model
        assert self._selection_model

        if node_id := self._selection_model.currentNode():
            for attr in node_attributes[node_id]:
                # create attribute editor
                if attr_widget := self._delegate.createAttributeEditor(self._node_editor, self._model, node_id, attr):
                    with signalsBlocked(attr_widget):
                        self._delegate.updateAttributeEditor(self._model, node_id, attr, attr_widget)

                    # add attr editor
                    self._attribute_editors[attr] = attr_widget

    def onNodeAttributesChanged(self, node_attributes:dict[Hashable, list[str]]):
        assert self._model
        assert self._selection_model

        if node_id := self._selection_model.currentNode():
            for attr in node_attributes[node_id]:
                ### update editor
                if attr_widget := self._attribute_editors.get(attr):
                    attr_widget.isDe
                    with signalsBlocked(attr_widget):
                        self._delegate.updateAttributeEditor(self._model, node_id, attr, attr_widget)

    def onNodeAttributesRemoved(self, node_attributes:dict[Hashable, list[str]]):
        assert self._model
        assert self._selection_model

        if node_id := self._selection_model.currentNode():
            for attr in node_attributes[node_id]:
                ### get editor
                attr_widget = self._attribute_editors[attr]

                ### remove editor
                self._delegate.deleteAttributeEditor(self._node_editor, attr_widget)
            
