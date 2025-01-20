from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel

class NXNodeInspectorDelegate(QObject):
    def createNodeEditor(self, model:NXGraphModel, node_id:Hashable)->QWidget:
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

    def createAttributeEditor(self, parent_node_editor:QWidget, model:NXGraphModel, node_id:Hashable, attr:str):
        assert parent_node_editor is not None
        attr_widget = QLineEdit()

        @attr_widget.textChanged.connect
        def _update_model(text, model=model, node_id=node_id, attr=attr):
            assert model
            model.updateNodeAttributes(node_id, **{attr: text})

        label_widget = self.createAttributeLabel(model, node_id, attr)
        attributes_layout = parent_node_editor.layout().itemAt(2)
        attributes_layout.addRow(label_widget, attr_widget)

        return attr_widget

    def deleteAttributeEditor(self, parent_node_editor, attr_widget):
        attributes_layout = parent_node_editor.layout().itemAt(2)
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