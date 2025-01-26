from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from networkx import node_boundary
from networkx.generators import line
from numpy import isin
from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel
from pylive.NetworkXGraphEditor.nx_graph_selection_model import (
    NXGraphSelectionModel
)
from pylive.NetworkXGraphEditor.nx_node_inspector_delegate import (
    NXNodeInspectorDelegate
)
from pylive.NetworkXGraphEditor.nx_graph_shapes import BaseNodeItem
from pylive.utils.unique import make_unique_name
from pylive.utils.qt import signalsBlocked

from bidict import bidict

type AttrId=str


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
        self._node_editors: bidict[Hashable, QWidget]=bidict()
        self._attribute_editors: bidict[AttrId, QLineEdit] = bidict()
        super().__init__(parent=parent)

        # Setup UI
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        # main_layout.addStretch()

        #
        self.setModel(model)
        self.setSelectionModel(selection)

    def _filtered_nodes(self):
        if self._selection_model:
            if current_node_id:=self._selection_model.selectedNodes():
                yield current_node_id

    def onSelectionChanged(self, selected, deselected):
        assert self._model
        assert self._selection_model

        ### create node editor
        main_layout = cast(QVBoxLayout, self.layout())

        if item:=main_layout.takeAt(0):
            if widget:=item.widget():
                widget.deleteLater()

        self._node_editors.clear()
        self._attribute_editors.clear()

        if node_id:=self._selection_model.currentNode():
            if node_editor := self._delegate.createNodeEditor(self._model, node_id):
                node_editor.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
                self._node_editors[node_id] = node_editor
                main_layout.insertWidget(0, node_editor)
                self._delegate.updateNodeEditor(self._model, node_id, node_editor)
                self.onNodeAttributesAdded({node_id: self._model.nodeAttributes(node_id)})

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

    def onNodeAttributesAdded(self, node_attributes:dict[Hashable, Iterable[AttrId]]):
        assert self._model
        assert self._selection_model

        if node_id := self._selection_model.currentNode():
            if node_id in node_attributes:
                for attr in node_attributes[node_id]:
                    # create attribute editor
                    if node_editor:=self._node_editors.get(node_id):
                        if attr_widget := self._delegate.createAttributeEditor(node_editor, self._model, node_id, attr):
                            with signalsBlocked(attr_widget):
                                self._delegate.updateAttributeEditor(self._model, node_id, attr, attr_widget)

                            # add attr editor
                            self._attribute_editors[attr] = attr_widget

    def onNodeAttributesChanged(self, node_attributes:dict[Hashable, list[str]]):
        assert self._model
        assert self._selection_model

        if node_id := self._selection_model.currentNode():
            if node_id in node_attributes:
                for attr in node_attributes[node_id]:
                    ### update editor
                    if attr_widget := self._attribute_editors.get(attr):
                        with signalsBlocked(attr_widget):
                            self._delegate.updateAttributeEditor(self._model, node_id, attr, attr_widget)

    def onNodeAttributesRemoved(self, node_attributes:dict[Hashable, list[str]]):
        assert self._model
        assert self._selection_model

        if node_id := self._selection_model.currentNode():
            if node_id in node_attributes:
                if node_editor:=self._node_editors.get(node_id):
                    for attr in node_attributes[node_id]:
                        ### get editor
                        attr_widget = self._attribute_editors[attr]

                        ### remove editor
                        self._delegate.deleteAttributeEditor(node_editor, attr_widget)
            
