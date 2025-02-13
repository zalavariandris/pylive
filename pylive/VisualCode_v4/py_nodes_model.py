
from collections import defaultdict
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from pylive.VisualCode_v4.py_fields_model import PyFieldsModel
from pylive.utils.evaluate_python import parse_python_function



import inspect
class UniqueFunctionItem:
    def __init__(self, source:str, name:str|None=None, fields:PyFieldsModel|None=None):
        self._source = source
        self._fields = fields or PyFieldsModel()
        self._name = name
        self._cached_func = None
        self._dirty = True

    def source(self):
        return self._source

    def name(self):
        return self._name

    def func(self):
        if not self._cached_func:
            self._cached_func = parse_python_function(self._source)
        return self._cached_func

    def setSource(self, source:str):
        self._source = source

    def inlets(self)->Sequence[str]:
        func = self.func()
        sig = inspect.signature(func)
        return tuple(_ for _ in sig.parameters)

    def fields(self):
        return self._fields

    def kind(self):
        return "UniqueFunction"

    def dirty(self):
        return self._dirty


class PyNodesModel(QAbstractItemModel):
    def __init__(self, parent: QObject|None=None) -> None:
        super().__init__(parent)
        self._node_items:list[UniqueFunctionItem] = []

    def inlets(self, row)->Sequence[str]:
        return self._node_items[row].inlets()

    def outlets(self, row)->Sequence[str]:
        return ["out"]
        
    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows in the model."""
        return len(self._node_items)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role==Qt.ItemDataRole.DisplayRole:
            return ["name", "definition", "dirty", "fields"][section]
        else:
            return super().headerData(section, orientation, role)

    def columnCount(self, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> int:
        return 1

    def data(self, index: QModelIndex|QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._node_items):
            return None

        item = self._node_items[index.row()]

        if index.column()==0:
            if role==Qt.ItemDataRole.DisplayRole:
                first_line = item.source().split("\n")[0]
                import re
                pattern = r"def\s+(?P<func_name>\w+)\s*\("
                match = re.search(pattern, first_line)
                if match:
                    return match.group("func_name") 
                else:
                    import textwrap
                    return textwrap.shorten(first_line, width=12, placeholder="...")

            elif role==Qt.ItemDataRole.EditRole:
                return item.source

        return None

    def setUniqueFunctionSource(self, index:QModelIndex, source:str):
        row = index.row()
        node_item = self._node_items[row]
        node_item.setSource(source)
        self.dataChanged.emit(
            index.siblingAtColumn(0), index.siblingAtColumn(0), 
            [
                Qt.ItemDataRole.DisplayRole, 
                Qt.ItemDataRole.EditRole,
                Qt.ItemDataRole.BackgroundRole
            ]
        )

    def setData(self, index: QModelIndex|QPersistentModelIndex, value:Any, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._node_items):
            return None

        item = self._node_items[index.row()]

        if index.column()==0:
            if role==Qt.ItemDataRole.EditRole:
                item.source = value

        # elif index.column()==1 and role==Qt.ItemDataRole.EditRole:
        #     item.label = str(value)

        # elif index.column()==2 and role==Qt.ItemDataRole.EditRole:
        #     item.dirty = bool(value)

        return None

    def insertRows(self, row:int, count:int, parent=QModelIndex()):
        if len(self._node_items) <= row or row < 0:
            return False

        self.beginInsertRows(parent, row, row + count - 1)
        for _ in range(count):
            node = UniqueFunctionItem(
                source="""def func():/n  ...""",
                fields=PyFieldsModel()
            )
            self._node_items.append(node)
        self.endInsertRows()
        return True

    def addNodeItem(self, item:UniqueFunctionItem):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._node_items.append(item)
        self.endInsertRows()

    def nodeItem(self, row)->UniqueFunctionItem:
        return self._node_items[row]

    def nodeItemFromIndex(self, index:QModelIndex)->UniqueFunctionItem|None:
        if index.isValid() and index.model() == self:
            row = index.row()
            if row>=0 and row < len(self._node_items):
                return self._node_items[row]

    def insertNodeItem(self, row:int, item:UniqueFunctionItem):
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

    def flags(self, index):
        """Returns the item flags for the given index."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable

    def index(self, row:int, column:int, parent=QModelIndex()):
        if parent.isValid():
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
    add_field_action = QAction("add",window)
    def add_field():
        model.insertNodeItem(0, UniqueFunctionItem("new node", QPersistentModelIndex(), PyFieldsModel(), True))

    add_field_action.triggered.connect(add_field)
    menubar = QMenuBar()
    menubar.addAction(add_field_action)
    main_layout.setMenuBar(menubar)
    main_layout.addWidget(table_view)
    main_layout.addWidget(list_view)
    window.setLayout(main_layout)
    window.show()
    app.exec()