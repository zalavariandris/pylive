
from collections import defaultdict
from typing import *
from typing_extensions import deprecated
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from networkx.classes import graphviews

from pylive.qt_options_dialog import QOptionDialog
from pylive.utils import group_consecutive_numbers
from pylive.utils.qt import modelReset, signalsBlocked


from dataclasses import dataclass, field
from fields_model import FieldsModel
from definitions_model import DefinitionsModel, DefinitionItem

@dataclass
class NodeItem:
    name: str
    #content
    definition: QPersistentModelIndex
    fields: FieldsModel
    dirty:bool


class NodesModel(QAbstractItemModel):
    ObjectRole = Qt.ItemDataRole.UserRole
    DefinitionRole = Qt.ItemDataRole.UserRole+1
    NameRole = Qt.ItemDataRole.UserRole+2
    FieldsRole = Qt.ItemDataRole.UserRole+3
    DirtyRole = Qt.ItemDataRole.UserRole+4

    def __init__(self, definitions:QAbstractItemModel, parent: QObject|None=None) -> None:
        super().__init__(parent)
        self._nodes:list[NodeItem] = []
        self._related_definitions = definitions

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows in the model."""
        return len(self._nodes)

    def columnCount(self, parent: QModelIndex|QPersistentModelIndex=QModelIndex()) -> int:
        return 3

    def data(self, index:QModelIndex|QPersistentModelIndex, role:Qt.ItemDataRole.DisplayRole):
        """Returns the data for the given index and role."""
        if not index.isValid() or not 0 <= index.row() < len(self._nodes):
            return None

        node = self._nodes[index.row()]

        match role:
            case Qt.ItemDataRole.DisplayRole:
                return node.name

            case Qt.ItemDataRole.UserRole:
                return node  # Return the entire person dictionary for custom use

            case self.NameRole:
                return node.name

            case self.DefinitionRole:
                return node.definition

            case self.DirtyRole:
                return node.dirty

            case self.FieldsRole:
                return node.fields
            case _:
                return None

    def roleNames(self)->dict[int, bytes]:
        """Returns a dictionary mapping custom role numbers to role names."""
        return {
            self.ObjectRole:             b'object',
            Qt.ItemDataRole.DisplayRole: b'name',
            self.DefinitionRole:         b'definition',
            self.DirtyRole:              b'dirty',
            self.FieldsRole:          b'fields'
        }

    def insertRows(self, row:int, count:int, parent=QModelIndex()):
        if len(self._nodes) <= row or row < 0:
            return False

        self.beginInsertRows(parent, row, row + count - 1)
        for _ in range(count):
            node = NodeItem(
                name= "",
                definition=QPersistentModelIndex(),
                dirty= True,
                fields= FieldsModel()
            )
            self._nodes.append(node)
        self.endInsertRows()
        return True

    def addNodeItem(self, name:str, definition:QModelIndex, fields:FieldsModel=FieldsModel()):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())

        self._nodes.append(NodeItem(
            name=name, 
            definition= QPersistentModelIndex(definition),
            dirty= True,
            fields=fields
        ))
        self.endInsertRows()

    def removeRows(self, row:int, count:int, parent=QModelIndex()):
        """Removes rows from the model."""
        if row < 0 or row + count > len(self._nodes):
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        for row in range(row+count-1, row, -1):
            del self._nodes[row]
        self.endRemoveRows()
        return True

    def clear(self):
        self.blockSignals(True)
        self.removeRows(0, self.rowCount(), QModelIndex())
        self.blockSignals(False)
        self.modelReset.emit()

    def flags(self, index):
        """Returns the item flags for the given index."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled ### | Qt.ItemFlag.ItemIsEditable

    def index(self, row:int, column:int, parent=QModelIndex()):
        if parent.isValid():
            return QModelIndex()

        return self.createIndex(row, column)

    def parent(self, index:QModelIndex|QPersistentModelIndex)->QModelIndex:
        return QModelIndex()  # No parent for this flat model


if __name__ == "__main__":
    app = QApplication()
    window = QWidget()
    main_layout = QHBoxLayout()
    model = NodesModel()
    table_view = QTableView()
    table_view.setModel(model)
    list_view = QListView()
    list_view.setModel(model)
    add_field_action = QAction("add",window)
    def add_field():
        model.insertNodeItem(0, NodeItem("new node", QPersistentModelIndex(), FieldsModel(), True))

    add_field_action.triggered.connect(add_field)
    menubar = QMenuBar()
    menubar.addAction(add_field_action)
    main_layout.setMenuBar(menubar)
    main_layout.addWidget(table_view)
    main_layout.addWidget(list_view)
    window.setLayout(main_layout)
    window.show()
    app.exec()