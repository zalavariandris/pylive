from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from dataclasses import dataclass, fields

@dataclass
class DefinitionItem:
    name: str
    source: str
    error: str|None=None


from enum import IntEnum
class DefinitionsModel(QAbstractItemModel):
    """Model for the detail view"""
    def __init__(self):
        super().__init__()
        self._definitions:list[DefinitionItem] = []

    def rowCount(self, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> int:
        return len(self._definitions)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role==Qt.ItemDataRole.DisplayRole:
            return ["name", "source", "error"][section]
        else:
            return super().headerData(section, orientation, role)

    def columnCount(self, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> int:
        return 3

    def data(self, index: QModelIndex|QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._definitions):
            return None

        item = self._definitions[index.row()]

        if role==Qt.ItemDataRole.DisplayRole or role==Qt.ItemDataRole.EditRole:
            match index.column():
                case 0:
                    return item.name
                case 1:
                    return item.source
                case 2:
                    return f"{item.error}"
        return None

    def setData(self, index: QModelIndex|QPersistentModelIndex, value:Any, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._definitions):
            return None

        item = self._definitions[index.row()]

        if role==Qt.ItemDataRole.DisplayRole or role==Qt.ItemDataRole.EditRole:
            match index.column():
                case 0:
                    item.name = value
                    self.dataChanged.emit(index, index, [role])
                    return True
                case 1:
                    item.source = value
                    self.dataChanged.emit(index, index, [role])
                    return True
                case 2:
                    item.error = value
                    self.dataChanged.emit(index, index, [role])
                    return True
        return None

    def insertDefinitionItem(self, row:int, item:DefinitionItem):
        self.beginInsertRows(QModelIndex(), row, row)
        self._definitions.insert(row, item)
        self.endInsertRows()
        return True

    def fieldItem(self, row:int):
        return self._definitions[row]

    def insertRows(self, row: int, count: int, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> bool:
        if len(self._definitions) <= row or row < 0:
            return False

        parent = QModelIndex()
        row = self.rowCount()
        count=1
        self.beginInsertRows(QModelIndex(), row, row+count-1)
        item = DefinitionItem("func", "def func()\n  ...", None)
        for row in range(row, row+count-1):
            self._definitions.insert(row, item)
        self.endInsertRows()
        return True

    def index(self, row: int, column: int, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        return self.createIndex(row, column)

    def parent(self, index: QModelIndex|QPersistentModelIndex) -> QModelIndex:
        return QModelIndex()

    def removeRows(self, row:int, count:int, parent=QModelIndex()):
        """Removes rows from the model."""
        if row < 0 or row + count > len(self._definitions):
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        for row in range(row+count-1, row, -1):
            del self._definitions[row]
        self.endRemoveRows()
        return True

    def flags(self, index: QModelIndex|QPersistentModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable

        return flags


if __name__ == "__main__":
    app = QApplication()
    window = QWidget()
    window.setWindowTitle("DefinitionsModel example")
    main_layout = QHBoxLayout()
    model = DefinitionsModel()
    table_view = QTableView()
    table_view.setModel(model)
    list_view = QListView()
    list_view.setModel(model)
    add_action = QAction("add",window)
    def add_item():
        model.insertDefinitionItem(0, DefinitionItem("hello", "def hello():\n  ...", None))

    add_action.triggered.connect(add_item)
    menubar = QMenuBar()
    menubar.addAction(add_action)
    main_layout.setMenuBar(menubar)
    main_layout.addWidget(table_view)
    main_layout.addWidget(list_view)
    window.setLayout(main_layout)
    window.show()
    app.exec()
