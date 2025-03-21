
from collections import defaultdict
import inspect
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from pylive.VisualCode_v4.py_fields_model import PyFieldsModel
from pylive.utils.evaluate_python import compile_python_function


from dataclasses import dataclass, field

@dataclass
class PyNodeItem:
    name:str
    code:str
    fields:dict[str, Any]=field(default_factory=dict)
    dirty:bool=True # code and fields dependent
    status:Literal["initalized", "compiled", "evaluated", "error"] = "initalized"

    # when compiled
    func:Callable|None = None
    inlets:list[str] = field(default_factory=list)

    # when evaluated
    result: object|None=None

    # when error
    error: Exception|None=None


class PyNodesModel(QAbstractItemModel):
    def __init__(self, parent: QObject|None=None) -> None:
        super().__init__(parent)
        self._node_items:list[PyNodeItem] = []
        self._headers = ["name", "code", "fields", "dirty", "status", "func", "inlets", "result", "error"]

    def inlets(self, row)->Sequence[str]:
        node_item = self._node_items[row]
        return node_item.inlets

    def outlets(self, row)->Sequence[str]:
        return ["out"]

    def rowCount(self, parent=QModelIndex())->int:
        """Returns the number of rows in the model."""
        return len(self._node_items)

    def columnCount(self, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role==Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        else:
            return super().headerData(section, orientation, role)

    def data(self, index: QModelIndex|QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._node_items):
            return None

        node_item = self._node_items[index.row()]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            attr = self.headerData(index.column(), Qt.Orientation.Horizontal)
            value = getattr(node_item, attr)
            match role:
                case Qt.ItemDataRole.DisplayRole:
                    if isinstance(value, (bool, str, int, float)):
                        return value
                    else:
                        return f"{value}"
                case Qt.ItemDataRole.EditRole:
                    return value
           
        return None

    def flags(self, index):
        """Returns the item flags for the given index."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        if index.column() in (0, 1):
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def dataByColumnName(self, row, column_name:str, role:int=Qt.ItemDataRole.DisplayRole):
        assert column_name in self._headers, f"{column_name} must be in headers: {self._headers}"
        column = self._headers.index(column_name)
        node_item = self._node_items[row]
        return getattr(node_item, column_name)

    def setDataByColumnName(self, row:int, column_name:str, value:Any, role:int=Qt.ItemDataRole.DisplayRole):
        assert column_name in self._headers, f"{column_name} must be in headers: {self._headers}"
        column = self._headers.index(column_name)
        self.setData(self.index(row, column), value)

    def setData(self, index: QModelIndex|QPersistentModelIndex, value:Any, role: int = Qt.ItemDataRole.DisplayRole) -> bool:
        if not index.isValid() or not 0 <= index.row() < len(self._node_items):
            return False

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            node_item = self._node_items[index.row()]
            column_name = self.headerData(index.column(), Qt.Orientation.Horizontal)
            if getattr(node_item, column_name) != value:
                setattr(node_item, column_name, value)
                self.dataChanged.emit(index, index)
                return True
                    
        return False

    def insertRows(self, row:int, count:int, parent:QModelIndex|QPersistentModelIndex=QModelIndex()):
        if len(self._node_items) <= row or row < 0:
            return False

        self.beginInsertRows(parent, row, row + count - 1)
        for _ in range(count):
            node = PyNodeItem(
                name="",
                code="""def func():/n  ..."""
            )
            self._node_items.append(node)
        self.endInsertRows()
        return True

    def nodeItem(self, row)->PyNodeItem:
        return self._node_items[row]

    def nodeItemFromIndex(self, index:QModelIndex)->PyNodeItem|None:
        if index.isValid() and index.model() == self:
            row = index.row()
            if row>=0 and row < len(self._node_items):
                return self._node_items[row]

    def insertNodeItem(self, row:int, item:PyNodeItem):
        self.beginInsertRows(QModelIndex(), row, row)
        self._node_items.insert(row, item)
        self.endInsertRows()
        return True

    def removeRows(self, row:int, count:int, parent=QModelIndex()):
        """Removes rows from the model."""
        if row < 0 or row + count > len(self._node_items):
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        for row in reversed(range(row, row+count)):
            del self._node_items[row]
        self.endRemoveRows()
        return True

    def clear(self):
        self.blockSignals(True)
        self.removeRows(0, self.rowCount(), QModelIndex())
        self.blockSignals(False)
        self.modelReset.emit()

    def index(self, row:int, column:int, parent=QModelIndex()):
        if parent.isValid():
            return QModelIndex()

        if row<0 or row >= len(self._node_items):
            return QModelIndex()

        return self.createIndex(row, column, self._node_items[row])

    def parent(self, index:QModelIndex|QPersistentModelIndex)->QModelIndex:
        return QModelIndex()  # No parent for this flat model






if __name__ == "__main__":
    app = QApplication()
    window = QWidget()
    main_layout = QHBoxLayout()
    model = PyNodesModel()
    table_view = QTableView()
    table_view.setModel(model)
    list_view = QListView()
    list_view.setModel(model)
    add_node_action = QAction("add",window)
    def add_node():
        node_item = PyNodeItem(
            name="",
            code="def func()\n  ...",
            error=None,
            dirty=True,
            fields=[]
        )

        model.insertNodeItem(0, node_item)

    add_node_action.triggered.connect(add_node)
    menubar = QMenuBar()
    menubar.addAction(add_node_action)
    main_layout.setMenuBar(menubar)
    main_layout.addWidget(table_view)
    main_layout.addWidget(list_view)
    window.setLayout(main_layout)
    window.show()
    app.exec()