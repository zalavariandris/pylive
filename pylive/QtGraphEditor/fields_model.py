from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *



from dataclasses import dataclass, fields

@dataclass
class FieldItem:
    name: str
    value: Any
    editable:bool=True


from enum import IntEnum
class FieldsModel(QAbstractItemModel):
    # class Roles(IntEnum):
    #     """Custom roles for detail view"""
    #     Name = Qt.ItemDataRole.DisplayRole
    #     Value = Qt.ItemDataRole.EditRole
    #     Object = Qt.ItemDataRole.UserRole
    #     Editable = Qt.ItemDataRole.UserRole+1

    """Model for the detail view"""
    def __init__(self):
        super().__init__()
        self._node:dict|None = None
        self._fields:list[FieldItem] = []

    def rowCount(self, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> int:
        return len(self._fields)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role==Qt.ItemDataRole.DisplayRole:
            return ["name", "value"][section]
        else:
            return super().headerData(section, orientation, role)

    def columnCount(self, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> int:
        return 2

    def data(self, index: QModelIndex|QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._fields):
            return None

        field = self._fields[index.row()]

        if index.column()==0 and role==Qt.ItemDataRole.DisplayRole:
            return f"{field.name}"

        elif index.column()==0 and role==Qt.ItemDataRole.EditRole:
            return field.name

        elif index.column()==1 and role==Qt.ItemDataRole.DisplayRole:
            return f"{field.value}"

        elif index.column()==1 and role==Qt.ItemDataRole.EditRole:
            return field.value

        elif role==Qt.ItemDataRole.UserRole:
            return field
        else:
            return None

    def setData(self, index: QModelIndex|QPersistentModelIndex, value:Any, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._fields):
            return None

        field = self._fields[index.row()]
        if index.column()==0:
            field.name = f"{value}"
            self.dataChanged.emit(index, index, [role])
            return True

        elif index.column()==1:
            field.value = value
            self.dataChanged.emit(index, index, [role])
            return True
            
        else:
            return False

    def insertFieldItem(self, row:int, field_item:FieldItem):
        self.beginInsertRows(QModelIndex(), row, row)
        self._fields.insert(row, field_item)
        self.endInsertRows()
        print("insertFieldItem", field_item)
        return True

    def fieldItem(self, row:int):
        return self._fields[row]

    def setNode(self, node: dict):
        """Update the model with a new person"""
        self.beginResetModel()
        self._node = node
        self.endResetModel()

    def insertRows(self, row: int, count: int, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> bool:
        if len(self._fields) <= row or row < 0:
            return False

        parent = QModelIndex()
        row = self.rowCount()
        count=1
        self.beginInsertRows(QModelIndex(), row, row+count-1)
        field_item = FieldItem("field", None)
        for row in range(row, row+count-1):
            self._fields.insert(row, field_item)
        self.endInsertRows()
        return True

    # def roleNames(self)->dict[int, bytes]:
    #     """Returns a dictionary mapping custom role numbers to role names."""
    #     return {
    #         Qt.ItemDataRole.DisplayRole: b'name',
    #         Qt.ItemDataRole.EditRole: b'value',
    #         self.Roles.Object:             b'object',
    #         self.Roles.Editable:             b'editable',
    #     }

    def index(self, row: int, column: int, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        return self.createIndex(row, column)

    def parent(self, index: QModelIndex|QPersistentModelIndex) -> QModelIndex:
        return QModelIndex()

    def removeRows(self, row:int, count:int, parent=QModelIndex()):
        """Removes rows from the model."""
        if row < 0 or row + count > len(self._fields):
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        for row in range(row+count-1, row, -1):
            del self._fields[row]
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
    main_layout = QHBoxLayout()
    fields_model = FieldsModel()
    fields_table_view = QTableView()
    fields_table_view.setModel(fields_model)
    fields_list_view = QListView()
    fields_list_view.setModel(fields_model)
    add_field_action = QAction("add",window)
    def add_field():
        fields_model.insertFieldItem(0, FieldItem("new field", 5, False))

    add_field_action.triggered.connect(add_field)
    menubar = QMenuBar()
    menubar.addAction(add_field_action)
    main_layout.setMenuBar(menubar)
    main_layout.addWidget(fields_table_view)
    main_layout.addWidget(fields_list_view)
    window.setLayout(main_layout)
    window.show()
    app.exec()

