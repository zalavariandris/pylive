
from collections import defaultdict
from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from pylive.VisualCode_v4.py_fields_model import PyFieldsModel
from pylive.utils.evaluate_python import parse_python_function


from dataclasses import dataclass

@dataclass
class PyNodeItem:
    name:str
    code:str
    error:Exception|None
    dirty:bool
    fields:PyFieldsModel
    _cached_func:Callable|None = None


class PyNodesModel(QAbstractItemModel):
    def __init__(self, parent: QObject|None=None) -> None:
        super().__init__(parent)
        self._node_items:list[PyNodeItem] = []

    def getNodeFunction(self, row:int)->Callable|None:
        node_item = self._node_items[row]
        if node_item._cached_func is None:
            try:
                node_item._cached_func = parse_python_function(node_item.code)
            except Exception as err:
                node_item._cached_func = None
        return node_item._cached_func

    def inlets(self, row)->Sequence[str]:
        if func:=self.getNodeFunction(row):
            import inspect
            print("inlets for function: ", func)
            sig = inspect.signature(func)
            return [name for name, param in sig.parameters.items()]
        return []

    def outlets(self, row)->Sequence[str]:
        return ["out"]
        
    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows in the model."""
        return len(self._node_items)

    def columnCount(self, parent: QModelIndex|QPersistentModelIndex = QModelIndex()) -> int:
        return 6

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role==Qt.ItemDataRole.DisplayRole:
            return ["name", "code", "inlets", "outlets", "dirty", "error"][section]
        else:
            return super().headerData(section, orientation, role)

    def data(self, index: QModelIndex|QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._node_items):
            return None

        node_item = self._node_items[index.row()]

        match index.column():
            case 0: # name
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return node_item.name

            case 1: # code
                if role==Qt.ItemDataRole.DisplayRole:
                    first_line = node_item.code.split("\n")[0]
                    import re
                    pattern = r"def\s+(?P<func_name>\w+)\s*\("
                    match = re.search(pattern, first_line)
                    if match:
                        return match.group("func_name") 
                    else:
                        import textwrap
                        return textwrap.shorten(first_line, width=12, placeholder="...")

                elif role==Qt.ItemDataRole.EditRole:
                    return node_item.code

            case 2: # inlets
                if role==Qt.ItemDataRole.DisplayRole:
                    return ", ".join(self.inlets(index.row()))

            case 3: # outlets
                if role==Qt.ItemDataRole.DisplayRole:
                    return ", ".join(self.outlets(index.row()))

            case 4: # dirty
                if role==Qt.ItemDataRole.DisplayRole:
                    return node_item.dirty

            case 5: # error
                if role==Qt.ItemDataRole.DisplayRole:
                    return f"{node_item.error}"

        return None

    def flags(self, index):
        """Returns the item flags for the given index."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        if index.column() in (0, 1):
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def setNodeCode(self, row:int, code:str):
        node_item = self._node_items[row]
        node_item.code = code
        index = self.index(row, 0)

        try:
            func = self.getNodeFunction(row)
            node_item._cached_func = func
            node_item.error = None
        except SyntaxError as err:
            node_item.error = err
        except Exception as err:
            node_item.error = err

        self.dataChanged.emit( # emit change for columns: code, inlets, outlets, dirty, error
            index.sibling(index.row(), 1), 
            index.sibling(index.row(), 5)
        )
        return True

    def setData(self, index: QModelIndex|QPersistentModelIndex, value:Any, role: int = Qt.ItemDataRole.DisplayRole) -> bool:
        if not index.isValid() or not 0 <= index.row() < len(self._node_items):
            return None

        node_item = self._node_items[index.row()]


        match index.column():
            case 0:
                if role == Qt.ItemDataRole.EditRole:
                    node_item.name = value
                    self.dataChanged.emit(
                        index.sibling(index.row(), 0), 
                        index.sibling(index.row(), 0)
                    )

                    return True
            case 1:
                if role == Qt.ItemDataRole.EditRole:
                    self.setNodeCode(index.row(), value)
                    return True
                    
        return False

    def insertRows(self, row:int, count:int, parent=QModelIndex()):
        if len(self._node_items) <= row or row < 0:
            return False

        self.beginInsertRows(parent, row, row + count - 1)
        for _ in range(count):
            node = PyNodeItem(
                name="",
                code="""def func():/n  ...""",
                error=None,
                dirty=False,
                fields=PyFieldsModel()
            )
            self._node_items.append(node)
        self.endInsertRows()
        return True

    def appendNodeItem(self, item:PyNodeItem):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._node_items.append(item)
        self.endInsertRows()

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
            fields=PyFieldsModel()
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