from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from networkx.generators import line
from pylive.NetworkXGraphEditor.nx_graph_model import NXGraphModel
from pylive.NetworkXGraphEditor.nx_graph_selection_model import (
    NXGraphSelectionModel,
)
from pylive.utils.unique import make_unique_name


class NXNodeInspectorView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self._model: NXGraphModel | None = None
        self._selectionModel: NXGraphSelectionModel | None = None

        # widgets
        self.kind_label = QLabel()
        self.name_label = QLabel()

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("new attribute")
        self.line_edit.returnPressed.connect(
            lambda: (
                self.addAttribute(self.line_edit.text()),
                self.line_edit.setText(""),
            )
        )
        self.remove_button = QPushButton("remove attribute")
        self.remove_button.clicked.connect(
            lambda: self.removeSelectedAttribute()
        )

        self.attributesTable = QTableWidget()
        self.attributesTable.setColumnCount(1)

        self._item_to_attribute: dict[QTableWidgetItem, str] = dict()
        self._attribute_to_item: dict[str, QTableWidgetItem] = dict()

        self.attributesForm = QFormLayout()

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
        main_layout = QVBoxLayout()
        header_layout = QHBoxLayout()
        header_layout.addWidget(self.kind_label)
        header_layout.addWidget(self.name_label)
        main_layout.addLayout(header_layout)

        main_layout.addWidget(QLabel("attributes"))
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.line_edit)
        buttonsLayout.addWidget(self.remove_button)
        main_layout.addLayout(buttonsLayout)
        main_layout.addWidget(self.attributesTable)
        main_layout.addLayout(self.attributesForm)
        main_layout.addStretch()

        self.setLayout(main_layout)

        self._attribute_to_row: dict[str, int] = dict()
        self._row_to_attribute: dict[int, str] = dict()

        self._widget_to_attribute: dict[QWidget, str] = dict()
        self._attribute_to_widget: dict[str, QWidget] = dict()

    def setModel(self, model: NXGraphModel):
        self._model = model

        model.nodesAdded.connect(lambda: self._updateView())
        model.nodesRemoved.connect(lambda: self._updateView())
        model.nodesChanged.connect(lambda: self._updateView())
        self._updateView()

    def setSelectionModel(self, selectionModel: NXGraphSelectionModel):
        selectionModel.selectionChanged.connect(lambda: self._updateView())
        self._selectionModel = selectionModel
        self._updateView()

    def _updateView(self):
        print("update view")
        """TODO: needs a ore refined updade mechanism"""
        n = self._get_current_node()
        if not n:
            self.kind_label.setText("")
            self.name_label.setText("- no selection -")

            self.attributesTable.clearContents()
            self.attributesTable.setRowCount(0)
            return

        ### update header
        self.kind_label.setText(f"{n.__class__}")
        self.name_label.setText(f"{n}")

        ### update attributes table
        self.attributesTable.clear()
        self.attributesTable.setHorizontalHeaderItem(
            0, QTableWidgetItem("value")
        )
        attributes = self._model.G.nodes[n]
        self.attributesTable.setRowCount(len(attributes))
        for row, (attr, value) in enumerate(attributes.items()):
            print(row, attr, value)
            name_item = QTableWidgetItem(
                f"{attr}",
            )
            self.attributesTable.setVerticalHeaderItem(row, name_item)
            # self.attributesTable.setItem(row, 0, item1)
            value_item = QTableWidgetItem(f"{value}")
            self.attributesTable.blockSignals(True)
            self.attributesTable.setItem(row, 0, value_item)
            self.attributesTable.blockSignals(False)
            self._row_to_attribute[row] = attr
            self._attribute_to_row[attr] = row

        ### update attributes form
        while self.attributesForm.count():
            item = self.attributesForm.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()

        attributes = self._model.G.nodes[n]
        for row, (attr, value) in enumerate(attributes.items()):
            lineedit = QLineEdit(f"{value}")
            self.attributesForm.addRow(attr, lineedit)

            def setModel(widget=lineedit, n=n, attr=attr):
                assert self._model
                self._model.setNodeProperties(n, **{attr: widget.text()})
                widget.clear()

            def setEditor(widget=lineedit, n=n, attr=attr):
                assert self._model
                value = self._model.getNodeProperty(n, attr)
                widget.setText(f"{value}")

            lineedit.editingFinished.connect(setModel)
            self._widget_to_attribute[lineedit] = attr
            self._attribute_to_widget[attr] = lineedit

    @Slot()
    def addAttribute(self, attr: str = "attr1", value=None):
        print("addAttribute", self._model, self._get_current_node())
        if not self._model:
            return

        n = self._get_current_node()

        if not n:
            return

        attributes = self._model.G.nodes[n]
        attr = make_unique_name(attr, attributes.keys())

        props = {attr: None}
        self._model.setNodeProperties(n, **props)

    @Slot()
    def removeSelectedAttribute(self):
        ...

    def _get_current_node(self):
        if not self._selectionModel:
            return None
        selection = self._selectionModel.selectedNodes()
        return selection[0] if selection else None
