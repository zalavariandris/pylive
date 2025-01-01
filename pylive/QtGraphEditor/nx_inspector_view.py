from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import * 
from pylive.QtGraphEditor.nx_graph_model import NXGraphModel
from pylive.QtGraphEditor.nx_graph_selection_model import NXGraphSelectionModel
from pylive.utils.unique import make_unique_name

class NXInspectorView(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self._model:NXGraphModel|None = None
        self._selectionModel:NXGraphSelectionModel|None = None

        # widgets
        self.kind_label = QLabel()
        self.name_label = QLabel()

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("new attribute")
        self.line_edit.returnPressed.connect(lambda: (
            self.addAttribute(self.line_edit.text()),
            self.line_edit.setText("")
        ))
        self.remove_button = QPushButton("remove attribute")
        self.remove_button.clicked.connect(lambda: self.removeSelectedAttribute())

        self.attributesTable = QTableWidget()
        self.attributesTable.setColumnCount(1)

        self._item_to_attribute:dict[QTableWidgetItem, str] = dict()
        self._attribute_to_item:dict[str, QTableWidgetItem] = dict()

        self.updateView()


        def on_item_changed(item):
            if not self._model:
                return
            n = self._get_current_node()
            if not n:
                return

            row = item.row()
            value = item.text()
            attr = self._row_to_attribute[row]
            change = {attr: value}
            print(f"set node properties: {n}, {change}")
            self._model.setNodeProperties(n, **change)

        self.attributesTable.itemChanged.connect(on_item_changed)

        # layout
        mainLayout = QVBoxLayout()
        header_layout = QHBoxLayout()
        header_layout.addWidget(self.kind_label)
        header_layout.addWidget(self.name_label)
        mainLayout.addLayout(header_layout)

        mainLayout.addWidget(QLabel("attributes"))
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.line_edit)
        buttonsLayout.addWidget(self.remove_button)
        mainLayout.addLayout(buttonsLayout)
        mainLayout.addWidget(self.attributesTable)
        mainLayout.addStretch()

        self.setLayout(mainLayout)

        self._attribute_to_row:dict[str, int] = dict()
        self._row_to_attribute:dict[int, str] = dict()

    def setModel(self, model:NXGraphModel):
        self._model = model
        
        model.nodesAdded.connect(lambda: self.updateView())
        model.nodesRemoved.connect(lambda: self.updateView())
        model.nodesPropertiesChanged.connect(lambda: self.updateView())
        self.updateView()

    def setSelectionModel(self, selectionModel:NXGraphSelectionModel):
        selectionModel.selectionChanged.connect(lambda: self.updateView())
        self._selectionModel = selectionModel
        self.updateView()

    def updateView(self):
        print("update view")
        n = self._get_current_node()
        if not n:   
            self.kind_label.setText("")
            self.name_label.setText("- no selection -")

            self.attributesTable.clearContents()
            self.attributesTable.setRowCount(0)
            return

        self.kind_label.setText(f"{n.__class__}")
        self.name_label.setText(f"{n}")
        self.attributesTable.clear()
        self.attributesTable.setHorizontalHeaderItem(0, QTableWidgetItem("value"))
        attributes = self._model.G.nodes[n]
        self.attributesTable.setRowCount( len(attributes) )
        
        print(attributes)
        for row, (attr, value) in enumerate(attributes.items()):
            print(row, attr, value)
            name_item = QTableWidgetItem(f"{attr}",)
            self.attributesTable.setVerticalHeaderItem(row, name_item)
            # self.attributesTable.setItem(row, 0, item1)
            value_item = QTableWidgetItem(f"{value}")
            self.attributesTable.blockSignals(True)
            self.attributesTable.setItem(row, 0, value_item)
            self.attributesTable.blockSignals(False)
            self._row_to_attribute[row] = attr
            self._attribute_to_row[attr] = row

    @Slot()
    def addAttribute(self, attr:str="attr1", value=None):
        print("addAttribute", self._model, self._get_current_node())
        if not self._model:
            return

        n = self._get_current_node()

        if not n:
            return

        attributes = self._model.G.nodes[n]
        attr = make_unique_name(attr, attributes.keys())

        props = {
            attr: None
        }
        self._model.setNodeProperties(n, **props)

    @Slot()
    def removeSelectedAttribute(self):
        ...

    def _get_current_node(self):
        if not self._selectionModel:
            return None
        selection = self._selectionModel.selectedNodes()
        return selection[0] if selection else None