from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from networkx.generators import line
from numpy import isin
from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel
from pylive.NetworkXGraphEditor.nx_graph_selection_model import (
    NXGraphSelectionModel,
)
from pylive.utils.unique import make_unique_name
from pylive.utils.qt import signalsBlocked

from bidict import bidict

type AttrId=str


class NXNodeInspectorDelegate(QObject):
    def createAttributeEditor(self, model, node_id, attr:str):
        # if isinstance(attr, str) and attr.startswith("_"):
        #     return None

        attr_widget = QLineEdit()

        @attr_widget.textChanged.connect
        def _update_model(text, model=model, node_id=node_id, attr=attr):
            assert model
            model.updateNodeAttributes(node_id, **{attr: text})

        return attr_widget

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
        self._attribute_editors: bidict[AttrId, QLineEdit] = bidict()
        super().__init__(parent=parent)

        # Setup UI
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        ### header
        self.header_label = QLabel("<h1>None</h1>")
        main_layout.addWidget(self.header_label)

        ### attributes
        self._new_attribute_edit = QLineEdit()
        self._new_attribute_edit.setPlaceholderText("new attribute")
        main_layout.addWidget(self._new_attribute_edit)

        @self._new_attribute_edit.returnPressed.connect
        def _add_attribute_to_current_node():
            assert self._model
            assert self._selection_model
            current_node_id = self._selection_model.currentNode()
            attr = self._new_attribute_edit.text()
            self._model.updateNodeAttributes(current_node_id, **{attr: None})
            self._new_attribute_edit.clear()

        self._attributes_layout = QFormLayout()
        main_layout.addLayout(self._attributes_layout)
        main_layout.addStretch()

        #
        self.setModel(model)
        self.setSelectionModel(selection)


    def setModel(self, model: NXGraphModel):
        if model:
            model.nodeAttributesAdded.connect(self.onNodeAttributesAdded)
            model.nodeAttributesAboutToBeRemoved.connect(self.onNodeAttributesRemoved)
            model.nodeAttributesChanged.connect(self.onNodeAttributesChanged)
        if self._model:
            model.nodeAttributesAdded.disconnect(self.onNodeAttributesAdded)
            model.nodeAttributesAboutToBeRemoved.disconnect(self.onNodeAttributesRemoved)
            model.nodeAttributesChanged.disconnect(self.onNodeAttributesChanged)
        self._model = model

    def setSelectionModel(self, selection_model: NXGraphSelectionModel):
        if selection_model:
            selection_model.selectionChanged.connect(self.onSelectionChanged)
        if self._selection_model:
            selection_model.selectionChanged.disconnect(self.onSelectionChanged)

        self._selection_model = selection_model

    def onSelectionChanged(self, selected, deselected):
        assert self._model
        assert self._selection_model

        ### create node editor
        current_node_id = self._selection_model.currentNode()
        self.header_label.setText(f"""\
            <h1>{current_node_id}</h1>""")

        ### Init node attribute editors
        # clear attribute layout
        while self._attributes_layout.count():
            item = self._attributes_layout.takeAt(0)
            if widget:=item.widget():
                widget.deleteLater()

        if current_node_id:
            self._new_attribute_edit.show()
            self.onNodeAttributesAdded({current_node_id: self._model.nodeAttributes(current_node_id)})
        else:
            self._new_attribute_edit.hide()

    def onNodeAttributesAdded(self, node_attributes:dict[Hashable, list[AttrId]]):
        assert self._model
        assert self._selection_model

        current_node_id = self._selection_model.currentNode()
        if current_node_id not in node_attributes:
            return

        for attr in node_attributes[current_node_id]:
            # create attribute editor
            if attr_widget := self._delegate.createAttributeEditor(self._model, current_node_id, attr):
                with signalsBlocked(attr_widget):
                    self._delegate.updateAttributeEditor(self._model, current_node_id, attr, attr_widget)

                # add attr editor
                attr_label = QLabel(attr)
                remove_btn = QPushButton("x")
                remove_btn.setFixedSize(22, 22)
                name_layout = QHBoxLayout()
                name_layout.setContentsMargins(0,0,0,0)
                name_layout.setSpacing(0)
                name_widget = QWidget()
                name_widget.setLayout(name_layout)
                name_layout.addWidget(remove_btn)
                name_layout.addWidget(attr_label)
                
                @remove_btn.pressed.connect
                def _(node_id=current_node_id, attr=attr):
                    assert self._model
                    self._model.deleteNodeAttribute(node_id, attr)
                self._attributes_layout.addRow(name_widget, attr_widget)
                self._attribute_editors[attr] = attr_widget

    def onNodeAttributesChanged(self, node_attributes:dict[Hashable, list[str]]):
        assert self._model
        assert self._selection_model

        current_node_id = self._selection_model.currentNode()
        if current_node_id not in node_attributes:
            return

        for attr in node_attributes[current_node_id]:
            ### update editor
            if attr_widget := self._attribute_editors.get(attr):
                with signalsBlocked(attr_widget):
                    self._delegate.updateAttributeEditor(self._model, current_node_id, attr, attr_widget)


    def onNodeAttributesRemoved(self, node_attributes:dict[Hashable, list[str]]):
        assert self._model
        assert self._selection_model

        print("onNodeAttributesRemoved")

        current_node_id = self._selection_model.currentNode()
        if current_node_id not in node_attributes:
            return

        for attr in node_attributes[current_node_id]:
            ### get editor
            attr_widget = self._attribute_editors[attr]

            ### remove editor
            self._attributes_layout.removeRow(attr_widget)

    



